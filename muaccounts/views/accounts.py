import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import mail_managers
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.views.generic.simple import direct_to_template
from django.views.generic.create_update import create_object, apply_extra_context, lookup_object
from django.shortcuts import get_object_or_404
from django.forms.models import modelform_factory
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from frontendadmin.views import add as frontend_add, change as frontend_edit, delete as frontend_del
from uni_form.helpers import FormHelper, Submit


from muaccounts.models import MUAccount
from muaccounts.forms import MUAccountForm
from muaccounts.utils import USE_SSO

@login_required
def claim_account(request):
    if request.muaccount.owner is not None:
        return HttpResponseForbidden()

    context = {
        'user': request.user,
        'muaccount': request.muaccount,
        'site': Site.objects.get_current(),
        }

    subject = render_to_string('muaccounts/claim_account_subject.txt', context)
    subject = ''.join(subject.splitlines()) # must not contain newlines
    message = render_to_string('muaccounts/claim_account_email.txt', context)
    mail_managers(subject, message)

    return direct_to_template(request, 'muaccounts/claim_sent.html')

def _domainify(value):
    # suggest a free subdomain name based on username.
    # Domainify username: lowercase, change non-alphanumeric to
    # dash, strip leading and trailing dashes
    dn = base = re.sub(r'[^a-z0-9-]+', '-', value.lower()).strip('-')
    taken_domains = set([
        mua.domain for mua in MUAccount.objects.filter(
            domain__contains=base).all() ])
    i = 0
    while dn in taken_domains:
        i += 1
        dn = '%s-%d' % (base, i)
    
    return dn

@login_required
def create_muaccount(request, form_class=MUAccountForm, initial=None, form_fields=None, form_exclude=None, *args, **kwargs):
    if MUAccount.objects.filter(owner=request.user).count() >= request.user.quotas.muaccounts:
        return HttpResponseForbidden()
    
    initial = initial or {}
    initial['owner'] = request.user.id
    initial['subdomain'] = _domainify(request.user.username)
    
    form_exclude = [] if form_exclude is None else list(form_exclude)
    if not request.user.has_perm('muaccounts.can_set_analytics_code'):
        form_exclude.append('analytics_code')
    if not request.user.has_perm('muaccounts.can_set_custom_domain'):
        form_exclude.append('domain')
    if not request.user.has_perm('muaccounts.can_set_public_status'):
        form_exclude.append('is_public')
    if not request.user.has_perm('muaccounts.can_set_bounty_status'):
        form_exclude.append('is_bounty')    
    
    form = modelform_factory(MUAccount, form=form_class, fields=form_fields, exclude=form_exclude)
    form.helper = FormHelper()
    form.helper.add_input(Submit('submit',_('Create')))
    form.helper.add_input(Submit('_cancel',_('Cancel')))
    
    return frontend_add(request, form_class=form, initial=initial, *args, **kwargs)

@login_required
def change_muaccount(request, instance_id, form_exclude=None, *args, **kwargs):
    obj = lookup_object(MUAccount, instance_id, None, None)
    if obj.owner != request.user:
        return HttpResponseForbidden()
    
    form_exclude = [] if form_exclude is None else list(form_exclude)
    if not request.user.has_perm('muaccounts.can_set_analytics_code'):
        form_exclude.append('analytics_code')
    if not request.user.has_perm('muaccounts.can_set_custom_domain'):
        form_exclude.append('domain')
    if not request.user.has_perm('muaccounts.can_set_public_status'):
        form_exclude.append('is_public')
    if not request.user.has_perm('muaccounts.can_set_bounty_status'):
        form_exclude.append('is_bounty')
    
    return frontend_edit(request, instance_id=instance_id, form_exclude=form_exclude, *args, **kwargs)

@login_required
def delete_muaccount(request, instance_id, *args, **kwargs):
    obj = lookup_object(MUAccount, instance_id, None, None)
    if obj.owner != request.user:
        return HttpResponseForbidden()
    
    return frontend_del(request, instance_id=instance_id, *args, **kwargs)

    
@login_required
def remove_member(request, user_id):
    if request.method <> 'POST': return HttpResponseForbidden()
    # We edit current user's MUAccount
    account = get_object_or_404(MUAccount, owner=request.user)

    # but if we're inside a MUAccount, we only allow editing that muaccount.
    if getattr(request, 'muaccount', account) <> account:
        return HttpResponseForbidden()

    user = get_object_or_404(User, id=user_id)
    if user in account.members.all():
        account.remove_member(user)

    return HttpResponseRedirect(reverse('muaccounts_manage_general'))
