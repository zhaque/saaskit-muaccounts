import re, socket

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.safestring import SafeUnicode
from django.utils.translation import ugettext as _

from friends.importer import import_vcards
from registration.forms import RegistrationFormUniqueEmail
from registration.signals import user_registered, user_activated
from emailconfirmation.models import EmailAddress

from models import MUAccount
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

        try: MUAccount.objects.get(subdomain=subdomain)
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
