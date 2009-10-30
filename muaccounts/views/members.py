
#based on pinax friends_app local app.

from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.views.generic.simple import direct_to_template
from django.contrib.auth import login, authenticate
from django.http import HttpResponse, Http404

from django.utils.translation import ugettext_lazy as _

from friends.models import JoinInvitation
from friends.forms import JoinRequestForm
from friends.importer import import_yahoo, import_google
from registration.views import activate
from registration.models import RegistrationProfile

from muaccounts.models import MUAccount
from muaccounts.forms import ImportVCardForm, InvitedRegistrationForm
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
def invite(request, form_class=JoinRequestForm, **kwargs):
    template_name = kwargs.get("template_name", "friends/invite.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "friends/invite_facebox.html"
        )

    join_request_form = form_class()
    if request.method == "POST":
        join_request_form = form_class(request.POST)
        if join_request_form.is_valid():
            join_request_form.save(request.user)
            return redirect('muaccounts_member_list')
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
def contacts(request, form_class=ImportVCardForm,
        template_name="friends/contacts.html"):
    if request.method == "POST":
        if request.POST["action"] == "upload_vcard":
            import_vcard_form = form_class(request.POST, request.FILES)
            if import_vcard_form.is_valid():
                imported, total = import_vcard_form.save(request.user)
                request.user.message_set.create(message=_("%(total)s vCards found, %(imported)s contacts imported.") % {'imported': imported, 'total': total})
                import_vcard_form = ImportVCardForm()
        else:
            import_vcard_form = form_class()
            if request.POST["action"] == "import_yahoo":
                bbauth_token = request.session.get('bbauth_token')
                del request.session['bbauth_token']
                if bbauth_token:
                    imported, total = import_yahoo(bbauth_token, request.user)
                    request.user.message_set.create(message=_("%(total)s people with email found, %(imported)s contacts imported.") % {'imported': imported, 'total': total})
            if request.POST["action"] == "import_google":
                authsub_token = request.session.get('authsub_token')
                del request.session['authsub_token']
                if authsub_token:
                    print "authsub_token --> ", authsub_token
                    imported, total = import_google(authsub_token, request.user)
                    request.user.message_set.create(message=_("%(total)s people with email found, %(imported)s contacts imported.") % {'imported': imported, 'total': total})
    else:
        import_vcard_form = form_class()
    
    return render_to_response(template_name, {
        "import_vcard_form": import_vcard_form,
        "bbauth_token": request.session.get('bbauth_token'),
        "authsub_token": request.session.get('authsub_token'),
    }, context_instance=RequestContext(request))
