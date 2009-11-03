
#based on pinax friends_app local app.

from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.views.generic.simple import direct_to_template
from django.contrib.auth import login
from django.http import Http404
from django.conf import settings
from django.core.urlresolvers import reverse

from django.utils.translation import ugettext_lazy as _

import gdata
from friends.models import JoinInvitation
from friends.importer import import_yahoo
from registration.views import activate
from registration.models import RegistrationProfile

from muaccounts.models import MUAccount
from muaccounts.forms import ImportVCardForm, InvitedRegistrationForm
from muaccounts.forms import MuJoinRequestForm, ImportCSVContactsForm, ImportGoogleContactsForm
from muaccounts.views import decorators

@decorators.owner_only
def member_list(request, template='friends/member_list.html'):
    account = get_object_or_404(MUAccount, owner=request.user)
    
    joins_sent = request.user.join_from.all().order_by("-sent")
    
    return direct_to_template(request, template=template, extra_context={
        'account': account,
        'member_list': account.members.all(),
        "joins_sent": joins_sent,
    })

@decorators.owner_only
def invite(request, form_class=MuJoinRequestForm, initial=None, **kwargs):
    template_name = kwargs.get("template_name", "friends/invite.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "friends/invite_facebox.html"
        )

    if request.method == "POST":
        join_request_form = form_class(request.POST)
        if join_request_form.is_valid():
            join_request_form.save(request.user)
            return redirect('muaccounts_member_list')
    else:
        join_request_form = form_class(initial=initial)

    return render_to_response(template_name, {
        "join_request_form": join_request_form,
        }, context_instance=RequestContext(request))

@decorators.public
def accept_join(request, confirmation_key, registration_form=InvitedRegistrationForm,
                registration_template_name='registration/registration_form.html'):
    join_invitation = get_object_or_404(JoinInvitation, confirmation_key = confirmation_key.lower())
    
    if tuple(request.muaccount.members.filter(email__iexact=join_invitation.contact.email)):
        return redirect('/') #May be we should show a message, but it shouldn't happens
    
    def _login_message_set_redirect(user, message, redirect_to):
        user.backend='django.contrib.auth.backends.ModelBackend'
        login(request, user)
        user.message_set.create(message=unicode(message))
        
        return redirect(redirect_to)
    
    try:
        ex_user = User.objects.get(email__iexact=join_invitation.contact.email)
    except User.DoesNotExist:
        if request.method == "POST":
            form = registration_form(request.POST)
            if form.is_valid():
                new_user, redirect_to = form.save(join_invitation)
                if not new_user.is_active:
                    return redirect(redirect_to or 'registration_complete')
                else:
                    request.muaccount.add_member(new_user)
                    return _login_message_set_redirect(new_user, 
                                       _("You was registered successfully."), 
                                       redirect_to or '/')
        else:
            form = registration_form(initial={"email": join_invitation.contact.email})
        
        return render_to_response(registration_template_name, {
                "form": form,
            }, context_instance=RequestContext(request))
    else:
        request.muaccount.add_member(ex_user)
        return _login_message_set_redirect(ex_user, 
                        _("You was added to this site successfully."), '/')

@decorators.public
def mu_activate(request, activation_key,
             template_name='registration/activate.html',
             extra_context=None):
    activation_key = activation_key.lower() # Normalize before trying anything with it.
    account, redirect_to = RegistrationProfile.objects.activate_user(activation_key)
    if not account:
        raise Http404('Wrong or expired activation key.')
    
    request.muaccount.add_member(account)
    response = activate(request, activation_key, template_name, extra_context)
    
@decorators.owner_only
def contacts(request, vcard_form=ImportVCardForm, cvs_form=ImportCSVContactsForm, 
             google_import_form=ImportGoogleContactsForm,
             template_name="friends/contacts.html"):
    
    import_forms = (
        ('upload_vcard', vcard_form, _("%(total)s vCards found, %(imported)s contacts imported."),
         _("Import vCard")),
        ('upload_cvs', cvs_form, _("%(total)s contacts found, %(imported)s contacts imported."),
         _("Import CVS")),
        ('import_google', google_import_form, _("%(total)s contacts found, %(imported)s contacts imported."),
         _("Import from Google Contacts")),
    )
    context = {'import_forms': []}
    
    for action, form_class, message, title in import_forms:
        reset_form = True
        if request.POST.get("action") == action:
            form = form_class(request.POST, request.FILES)
            if form.is_valid():
                imported, total = form.save(request.user)
                request.user.message_set.create(message=message % {'imported': imported, 'total': total})
            else:
                reset_form = False
        
        if reset_form:
            form = form_class()
        
        context['import_forms'].append({'form': form, 'action': action, 'title': title})
        

    import_services = (
        ('import_yahoo', 'bbauth_token', import_yahoo, 
         _("Import from Yahoo Address Book"), reverse('bbauth_login')),
    )
    context['import_services'] = []
    
    for action, token_name, import_func, title, auth_url in import_services:
        token = request.session.get(token_name)
        if request.POST.get("action") == action:
            del request.session[token_name]
            if token:
                imported, total = import_func(token, request.user)
                request.user.message_set.create(
                        message=_("%(total)s people with email found, %(imported)s contacts imported.") \
                                     % {'imported': imported, 'total': total})
        context['import_services'].append({'title': title, 'token': token, 
                                           'action': action, 'auth_url': auth_url})
            
    return render_to_response(template_name, context, context_instance=RequestContext(request))
