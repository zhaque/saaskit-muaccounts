import re, socket, csv
from random import random

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.safestring import SafeUnicode
from django.utils.translation import ugettext as _
from django.utils.hashcompat import sha_constructor
from django.template.loader import render_to_string

from gdata.contacts.service import ContactsService
import gdata
from friends.importer import import_vcards
from friends.models import Contact, JoinInvitation, send_mail
from friends.forms import JoinRequestForm
from registration.forms import RegistrationFormUniqueEmail
from registration.signals import user_registered, user_activated
from emailconfirmation.models import EmailAddress

from muaccounts.models import MUAccount
from themes import ThemeField

class SubdomainInput(forms.TextInput):

    def render(self, *args, **kwargs):
        return SafeUnicode(
            super(SubdomainInput,self).render(*args,**kwargs)
            + MUAccount.subdomain_root )


class MUAccountCreateForm(forms.Form):
    name = forms.CharField()
    subdomain = forms.CharField(widget=SubdomainInput)

    _subdomain_re = re.compile('^[a-z0-9][a-z0-9-]+[a-z0-9]$')
    def clean_subdomain(self):
        subdomain = self.cleaned_data['subdomain'].lower().strip()

        if not self._subdomain_re.match(subdomain):
            raise forms.ValidationError(
                _('Invalid subdomain name.  You may only use a-z, 0-9, and "-".'))

        for pattern in getattr(settings, 'MUACCOUNTS_SUBDOMAIN_STOPWORDS', ('www',)):
            if re.search(pattern, subdomain, re.I):
                raise forms.ValidationError(
                    _('It is not allowed to use this domain name.'))

        try: 
            MUAccount.objects.get(subdomain=subdomain)
        except MUAccount.DoesNotExist: pass
        else: raise forms.ValidationError(
            _('An account with this subdomain already exists.'))

        return subdomain

    def get_instance(self, user):
        if self.is_valid():
            return MUAccount.objects.create(
                owner=user,
                name=self.cleaned_data['name'],
                subdomain=self.cleaned_data['subdomain'],
                )

_muaform_exclude = ('owner', 'members', 'subdomain')
if not getattr(settings, 'MUACCOUNTS_THEMES', None):
    _muaform_exclude += ('theme',)

class MUAccountForm(forms.ModelForm):
    theme = ('theme' in _muaform_exclude) or ThemeField()
    class Meta:
        model = MUAccount
        exclude = _muaform_exclude

    def __init__(self, *args, **kwargs):
        super(MUAccountForm, self).__init__(*args, **kwargs)
        if not self.instance.owner.has_perm('muaccounts.can_set_custom_domain'):
            self.fields['domain'].widget = forms.HiddenInput()
        if not self.instance.owner.has_perm('muaccounts.can_set_public_status'):
            self.fields['is_public'].widget = forms.HiddenInput()
        # no need to change values, they'll be forced to True when validating.

    _domain_re = re.compile(r'^[a-z0-9][a-z0-9-]*\.[a-z0-9-.]+[a-z0-9]$')
    def clean_domain(self):
        if not self.instance.owner.has_perm('muaccounts.can_set_custom_domain'):
            return self.instance.domain

        d = self.cleaned_data['domain'].strip().lower()

        if not self._domain_re.match(d):
            raise forms.ValidationError('Invalid domain name.')

        if d.endswith(MUAccount.subdomain_root):
            raise forms.ValidationError(
                _('You cannot set subdomain of %s.') % MUAccount.subdomain_root)

        try:
            ip = socket.gethostbyname(d)
            if hasattr(settings, 'MUACCOUNTS_IP'):
                if callable(settings.MUACCOUNTS_IP):
                    if not settings.MUACCOUNTS_IP(ip):
                        self._errors['domain'] = forms.util.ErrorList([
                            _('Domain %s does not resolve to a correct IP number.') % d ])
                else:
                    if ip <> settings.MUACCOUNTS_IP:
                        self._errors['domain'] = forms.util.ErrorList([
                            _('Domain %(domain)s does not resolve to %(ip)s.') % {'domain':d, 'ip':settings.MUACCOUNTS_IP} ])
        except socket.error, msg:
            self._errors['domain'] = forms.util.ErrorList([
                _('Cannot resolve domain %(domain)s: %(error_string)s')%{'domain':d,'error_string':msg} ])

        return d

    def clean_is_public(self):
        if self.instance.owner.has_perm('muaccounts.can_set_public_status'):
            return self.cleaned_data['is_public']
        return self.instance.is_public

class AddUserForm(forms.Form):
    user = forms.CharField(label='User',
                           help_text='Enter login name or e-mail address',
                           )
    def __init__(self, *args, **kwargs):
        try: self.muaccount = kwargs['muaccount']
        except KeyError: pass
        else: del kwargs['muaccount']
        super(AddUserForm, self).__init__(*args, **kwargs)

    def clean_user(self):
        un = self.cleaned_data['user']
        try:
            if '@' in un: u = User.objects.get(email=un)
            else: u = User.objects.get(username=un)
        except User.DoesNotExist:
            raise forms.ValidationError(_('User does not exist.'))
        if u == self.muaccount.owner:
            raise forms.ValidationError(_('You are already the plan owner.'))
        return u

    def clean(self):
        try:
            limit = self.muaccount.owner.quotas.muaccount_members
        except AttributeError: pass
        else:
            if limit <= len(self.muaccount.members.all()):
                raise forms.ValidationError(_("Member limit reached."))
        return self.cleaned_data


class StylesForm(forms.Form):
    WIDTHS = (
        ('doc3', '100% fluid'),
        ('doc', '750px centered'),
        ('doc2', '950px centered'),
        ('doc4', '974px fluid'),
    )

    COLORS = (
        ('aqua', 'Aqua'),
        ('green', 'Green'),
        ('purple', 'Purple'),
        ('red', 'Red'),
        ('tan-blue', 'Tan Blue'),
        ('default', 'CrowdSense'),
        ('fireflynight', 'Firefly Night'),
        ('freshair', 'Fresh Air'),
        ('girly', 'Girly'),
        ('grayscale', 'Grayscale'),
        ('grayscalem', 'Grayscale Modified'),
        ('overcast', 'Overcast'),
        ('pepper', 'Pepper'),
        ('sunshine', 'Sunshine'),
    )

    LAYOUTS = (
        ('yui-t6', 'Right sidebar, 300px'),
        ('yui-t1', 'Left sidebar, 160px'),
        ('yui-t2', 'Left sidebar, 180px'),
        ('yui-t3', 'Left sidebar, 300px'),
        ('yui-t4', 'Right sidebar, 180px'),
        ('yui-t5', 'Right sidebar, 240px'),
        ('yui-t0', 'Single Column'),
    )

    ON_OFF = (
        ('on', 'On'),
        ('off', 'Off'),
    )

    color_scheme = forms.ChoiceField(choices=COLORS)
    page_width = forms.ChoiceField(choices=WIDTHS)
    layout = forms.ChoiceField(choices=LAYOUTS)
    rounded_corners = forms.ChoiceField(choices=ON_OFF)

# @@@ move to django-friends when ready

class ImportVCardForm(forms.Form):

    vcard_file = forms.FileField(label="vCard File")

    def save(self, user):
        imported, total = import_vcards(self.cleaned_data["vcard_file"].content, user)
        return imported, total

class ImportCSVContactsForm(forms.Form):
    
    csv_file = forms.FileField(label=_("CSV file"),
        help_text = _("Format of each row: \"contact name\",\"e-mail address\". Rows with wrong format will be skiped."))
    
    def clean_csv_file(self):
        """just iterate over file"""
        try:
            for row in csv.reader(self.cleaned_data['csv_file']):
                pass
        except csv.Error, msg:
            print msg
            raise forms.ValidationError(_("Error while reading. Check your file."))
                
        return self.cleaned_data['csv_file']
    
    def save(self, user):
        total, imported = 0, 0
        for row in csv.reader(self.cleaned_data['csv_file']):
            if row:
                try:
                    name, email = row
                except ValueError:
                    #default behaviour
                    continue
                
                total +=1
                try:
                    Contact.objects.get(user=user, email=email)
                except Contact.DoesNotExist:
                    Contact(user=user, name=name, email=email).save()
                    imported += 1
        return imported, total

class ImportGoogleContactsForm(forms.Form):
    
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    
    def clean(self):
        if 'email' in self.cleaned_data and 'password' in self.cleaned_data:
            contacts_service = ContactsService(self.cleaned_data['email'], self.cleaned_data['password'])
            try:
                contacts_service.ProgrammaticLogin()
            except gdata.service.BadAuthentication, msg:
                raise forms.ValidationError(_(u'Incorrect Google account credentials'))
        return self.cleaned_data
    
    def save(self, user):
        contacts_service = ContactsService(self.cleaned_data['email'], self.cleaned_data['password'])
        contacts_service.ProgrammaticLogin()
        #based on django-friends importer module
        entries = []
        feed = contacts_service.GetContactsFeed()
        entries.extend(feed.entry)
        next_link = feed.GetNextLink()
        while next_link:
            feed = contacts_service.GetContactsFeed(uri=next_link.href)
            entries.extend(feed.entry)
            next_link = feed.GetNextLink()
        total = 0
        imported = 0
        for entry in entries:
            name = entry.title.text
            for e in entry.email:
                email = e.address
                total += 1
                try:
                    Contact.objects.get(user=user, email=email)
                except Contact.DoesNotExist:
                    Contact(user=user, name=name, email=email).save()
                    imported += 1
        return imported, total

_existing_emails = lambda muaccount: EmailAddress.objects.filter(
                                                    user__muaccount_member = muaccount, 
                                                    verified=True)
class MuJoinRequestForm(forms.Form):
    
    email = forms.EmailField(label=_("Email"), required=False, widget=forms.TextInput(attrs={'size':'30'}))
    contacts = forms.models.ModelMultipleChoiceField(queryset=Contact.objects.all(),
                                                     required=False, label=_('contacts'))
    message = forms.CharField(label="Message", required=False, 
                              widget=forms.Textarea(attrs = {'cols': '30', 'rows': '5'}))
    muaccount = forms.IntegerField(widget=forms.HiddenInput())
    
    def __init__(self, data=None, files=None, initial=None, *args, **kwargs):
        super(MuJoinRequestForm, self).__init__(data=data, files=files, initial=initial, *args, **kwargs)
        muaccount = self.data.get('muaccount') or self.initial.get('muaccount')
        self.fields['contacts'].queryset = self.fields['contacts'].queryset\
                .filter(user__owned_sites=muaccount)\
                .exclude(email__in=_existing_emails(muaccount).values_list('email', flat=True))
    
    def clean(self):
        # @@@ this assumes email-confirmation is being used
        if 'email' in self.cleaned_data:
            try:
                existing_email = _existing_emails(self.cleaned_data['muaccount'])\
                                       .get(email=self.cleaned_data['email'])
            except EmailAddress.DoesNotExist:
                pass
            else:
                self._errors['email'] = self.error_class([_(u"User with this e-mail address is already registered.")])
                del self.cleaned_data['email']
            
        return self.cleaned_data
    
    def save(self, user):
        contacts = self.cleaned_data.get('contacts', [])
        if self.cleaned_data.get('email'):
            contact = Contact.objects.get_or_create(email=self.cleaned_data['email'], user=user)
            if contact not in contacts:
                contacts.append(contact)
        
        muaccount = MUAccount.objects.get(id=self.cleaned_data['muaccount'])
        message = self.cleaned_data['message']
        context = {
            "SITE_NAME": muaccount.name,
            "CONTACT_EMAIL": user.email or settings.CONTACT_EMAIL,
            "user": user,
            "message": message,
        }
        
        for contact in contacts:
            #BASED ON django-friends JoinInvitationManager's method 'send_invitation' 
            contact, created = Contact.objects.get_or_create(email=contact.email, user=user)
            salt = sha_constructor(str(random())).hexdigest()[:5]
            confirmation_key = sha_constructor(salt + contact.email).hexdigest()
            context['accept_url'] = muaccount.get_absolute_url('friends_accept_join', 
                                                               args=(confirmation_key,))
            
            subject = render_to_string("friends/join_invite_subject.txt", context)
            email_message = render_to_string("friends/join_invite_message.txt", context)
            
            send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, [contact.email])        
            join_request = JoinInvitation.objects.create(from_user=user, contact=contact, 
                                                 message=message, status="2", 
                                                 confirmation_key=confirmation_key)
            user.message_set.create(message=_("Invitation to join sent to %(email)s") 
                                                % {'email':contact.email})

class InvitedRegistrationForm(RegistrationFormUniqueEmail):
    
    def save(self, join_invitation):
        email = self.cleaned_data['email']
        
        same_email = join_invitation.contact.email == email
        
        if same_email:
            new_user = User.objects.create_user(self.cleaned_data['username'], email=email, password=self.cleaned_data['password1'])
            user_registered.send(sender=User, user=new_user)
            user_activated.send(sender=User, user=new_user)
            EmailAddress(user=new_user, email=email, verified=True, primary=True).save()
        else:
            new_user = super(InvitedRegistrationForm, self).save()
            join_invitation.accept(new_user)
            EmailAddress(user=new_user, email=email, primary=True).save()
        
        return new_user, self.cleaned_data.get('redirect_to')
