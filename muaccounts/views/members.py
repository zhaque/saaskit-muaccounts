
#based on pinax friends_app local app.

from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.shortcuts import redirect, render_to_response
from django.contrib.auth.models import User
from django.views.generic.simple import direct_to_template
from django.views.generic.create_update import apply_extra_context
from django.contrib.auth import login, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.http import Http404
#from django.conf import settings
from django.core.urlresolvers import reverse

from django.utils.translation import ugettext, ugettext_lazy as _

from friends.models import JoinInvitation
from friends.importer import import_yahoo

from muaccounts.models import MUAccount, InvitationRequest
from muaccounts.forms import ImportVCardForm, InvitationRequestForm
from muaccounts.forms import MuJoinRequestForm, ImportCSVContactsForm, ImportGoogleContactsForm
from muaccounts.views import decorators

@login_required
@decorators.owner_only
def member_list(request, template='friends/member_list.html'):
    
    invitations_sent = request.user.join_from.all().order_by("-sent")
    joins_received = InvitationRequest.objects.filter(muaccount=request.muaccount, 
                                                      state=InvitationRequest.STATE_INIT)\
                                              .order_by("state", "-created")
    
    return direct_to_template(request, template=template, extra_context={
        'member_list': request.muaccount.members.all(),
        "invitations_sent": invitations_sent,
        "joins_received": joins_received,
    })

@login_required
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

@login_required
@decorators.public
def accept_join(request, confirmation_key):
    join_invitation = get_object_or_404(JoinInvitation, confirmation_key = confirmation_key.lower())
    
    if request.user.email == join_invitation.contact.email:
        join_invitation.accept(request.user)
        request.muaccount.add_member(request.user)
        request.user.message_set.create(message=ugettext("You was added to this site successfully."))
        return redirect('/')
    else:
        raise Http404('wrong e-mail')

@login_required
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
        

    import_services = []
    if request.muaccount.yahoo_app_id and request.muaccount.yahoo_secret:
        import_services.append(('import_yahoo', 'bbauth_token', import_yahoo, 
         _("Import from Yahoo Address Book"), reverse('bbauth_login')))
        
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


@decorators.public
def invitation_request(request, form_class=InvitationRequestForm, template_name="join_request.html",
                 extra_context=None):
    
    if request.user.is_authenticated() \
    and request.muaccount.members.filter(username=request.user.username).count():
        return redirect('/')
    
    request_obj, form = None, None
    
    def _get_request_obj(muaccount, email):
        try:
            return InvitationRequest.objects.get(muaccount=muaccount, email=email)
        except InvitationRequest.DoesNotExist:
            pass
    
    if request.user.is_authenticated():
        request_obj = _get_request_obj(request.muaccount, request.user.email)
    
    if request_obj is None:
        if request.method == "POST":
            form = form_class(request.POST)
            if form.is_valid():
                request_obj = form.save()
                form = None
            
            if request.POST.get('email'):
                request_obj = _get_request_obj(request.muaccount, request.POST['email'])
        else:
            initial={'muaccount': request.muaccount.id}
            if request.user.is_authenticated():
                initial['email'] = request.user.email
            form = form_class(initial=initial)
        
    context = {'form': form, 'join_request': request_obj}
    apply_extra_context(extra_context or {}, context)
    
    return render_to_response(template_name, context, context_instance=RequestContext(request))

@login_required
@decorators.owner_only
def change_invitation_request_state(request, email, state, 
                                    queryset=InvitationRequest.objects.all(),
                                    form_class=MuJoinRequestForm,
                                    redirect_to='muaccounts_member_list'):
    jr = get_object_or_404(queryset, email=email, muaccount=request.muaccount)
    if state == "invite":
        jr.set_invited()
        form = form_class({'muaccount':jr.muaccount.id, 
                        'message': jr.notes,
                        'email': jr.email})
        if form.is_valid(): 
            form.save(request.user)
    elif state == "reject":
        jr.set_rejected()
    else:
        raise Http404()
    
    return redirect(redirect_to)
