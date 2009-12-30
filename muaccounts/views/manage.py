from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.views.generic.create_update import update_object, apply_extra_context
from django.forms.models import modelform_factory
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect

from uni_form.helpers import FormHelper, Fieldset

from muaccounts.models import MUAccount
from muaccounts.forms import MUAccountForm

from muaccounts.views import decorators

@decorators.owner_only
def advanced_settings(request, form_class=MUAccountForm):
    fields = ['webmaster_tools_code', 'yahoo_app_id', 'yahoo_secret']

    if request.user.has_perm('muaccounts.can_set_analytics_code'):
        fields.append('analytics_code')
    if request.user.has_perm('muaccounts.can_set_custom_domain'):
        fields.append('domain')
    if request.user.has_perm('muaccounts.can_set_public_status'):
        fields.append('is_public')
    if request.user.has_perm('muaccounts.can_set_bounty_status'):
        fields.append('is_bounty')

    return update_object(request,
        form_class=modelform_factory(MUAccount, form=form_class, fields=fields),
        object_id=request.muaccount.pk,
        post_save_redirect=reverse('muaccounts_manage_advanced'),
        template_name='muaccounts/site_settings.html',
        extra_context={
            'title': _('Advanced'),
        }
    )

@decorators.owner_only
def general_settings(request, form_class=MUAccountForm):
    fields = ['name', 'tag_line', 'about', 'logo', 'language']
    exclude = ('theme',)

    return update_object(request, 
        form_class=modelform_factory(MUAccount, form=form_class, fields=fields),
        object_id=request.muaccount.pk,
        post_save_redirect=reverse('muaccounts_manage_general'),
        template_name='muaccounts/site_settings.html',
        extra_context={
            'title': _('General'),
        }
    )

@decorators.owner_only
def styles_settings(request, form_class=MUAccountForm):
    
    fields = ('theme',)
    
    ThemeForm = modelform_factory(MUAccount, form=form_class, fields=fields)
    ThemeForm.helper = FormHelper()
    
    return update_object(request, 
        form_class=ThemeForm,
        object_id=request.muaccount.pk,
        post_save_redirect=reverse('muaccounts_manage_styles'),
        template_name='muaccounts/site_settings.html',
        extra_context={
            'title': _('Color & Styles'),
        }
    )
    
