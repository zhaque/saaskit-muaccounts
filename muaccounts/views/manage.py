from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from muaccounts.models import MUAccount
from django.http import HttpResponseRedirect, HttpResponseForbidden
from muaccounts.forms import MUAccountForm, AddUserForm, StylesForm
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.views.generic.create_update import update_object
from django.forms.models import modelform_factory
from django.shortcuts import redirect
import decorators

@login_required
def account_detail(request, return_to=None, extra_context={}):
    # We edit current user's MUAccount
    account = get_object_or_404(MUAccount, owner=request.user)

    # but if we're inside a MUAccount, we only allow editing that muaccount.
    if getattr(request, 'muaccount', account) <> account:
        return HttpResponseForbidden()

    if return_to is None:
        return_to = reverse('muaccounts.views.account_detail')

    if 'domain' in request.POST:
        form = MUAccountForm(request.POST, request.FILES, instance=account)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(return_to)
    else:
        form = MUAccountForm(instance=account)

    if 'user' in request.POST:
        uform = AddUserForm(request.POST, muaccount=account)
        if uform.is_valid():
            account.add_member(uform.cleaned_data['user'])
            return HttpResponseRedirect(return_to)
    else:
        uform = AddUserForm()

    ctx = dict(object=account, form=form, add_user_form=uform)
    ctx.update(extra_context)

    return direct_to_template(
        request, template='muaccounts/account_detail.html',
        extra_context=ctx)

@decorators.owner_only
def member_list(request, template='muaccounts/member_list.html'):
    account = get_object_or_404(MUAccount, owner=request.user)
    return direct_to_template(request, template=template, extra_context={
        'account': account,
        'member_list': account.members.all(),
        'user': request.user,
    })

@decorators.owner_only
def add_member(request, template='muaccounts/manage/form.html',
                                    return_to='muaccounts_member_list'):
    account = get_object_or_404(MUAccount, owner=request.user)
    if request.method == 'POST':
        form = AddUserForm(request.POST, muaccount=account)
        if form.is_valid():
            account.add_member(form.cleaned_data['user'])
            return redirect(return_to)
    else:
        form = AddUserForm()
    return direct_to_template(request, template=template, extra_context={
        'form': form,
    })

@decorators.owner_only
def advanced_settings(request):
    fields = ['webmaster_tools_code', 'analytics_code']

    if request.user.has_perm('muaccounts.can_set_custom_domain'):
        fields.append('domain')

    if request.user.has_perm('muaccounts.can_set_adsense_code'):
        fields.append('adsense_code')

    return update_object(request,
        form_class=modelform_factory(MUAccount, fields=fields),
        object_id=request.muaccount.pk,
        post_save_redirect=reverse('muaccounts_manage_advanced'),
        template_name='muaccounts/manage/form.html',
        extra_context={
            'title': 'Advanced settings',
        }
    )

@decorators.owner_only
def general_settings(request):
    fields = ['name', 'tag_line', 'about', 'logo']

    if request.user.has_perm('muaccounts.can_set_public_status'):
        fields.append('is_public')


    return update_object(request,
        form_class=modelform_factory(MUAccount, fields=fields),
        object_id=request.muaccount.pk,
        post_save_redirect=reverse('muaccounts_manage_general'),
        template_name='muaccounts/manage/form.html',
        extra_context={
            'title': 'General settings',
        }
    )

@decorators.owner_only
def styles_settings(request):
    if request.method == 'POST':
        form = StylesForm(request.POST)
        if form.is_valid():
            request.muaccount.theme = form.cleaned_data
            request.muaccount.save()
    else:
        form = StylesForm(initial=request.muaccount.theme)
    return render_to_response("muaccounts/manage/form.html", {
        'form': form,
        'title': 'Color&Styles',
    }, context_instance=RequestContext(request))
