from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from muaccounts.views import members

def mu_initial(func):
    def wrapped(request, initial=None, *args, **kwargs):
        if initial is None: initial = {}
        initial['muaccount'] = request.muaccount.id
        return func(request, initial=initial, *args, **kwargs)
    
    return wrapped


urlpatterns = patterns('',
    url(r'^remove_member/(?P<user_id>\d+)/$', 'muaccounts.views.remove_member',
        name='muaccounts_remove_member'),

    url(r'^claim/$', 'muaccounts.views.claim_account',
        name='muaccounts_claim_account'),

    url(r'^advanced/$', 'muaccounts.views.advanced_settings',
        name='muaccounts_manage_advanced'),

    url(r'^general/$', 'muaccounts.views.general_settings',
        name='muaccounts_manage_general'),

    url(r'^styles/$', 'muaccounts.views.styles_settings',
        name='muaccounts_manage_styles'),
    
    #django-friends related views
    url(r'^users/$', 'muaccounts.views.members.member_list',
        name='muaccounts_member_list'),
    url(r'^invite/$', mu_initial(members.invite), name="muaccounts_add_member"),
    
    url(r'^accept/(\w+)/$', 'muaccounts.views.members.accept_join', name='friends_accept_join'),
    
    url(r'^contacts/$', 'muaccounts.views.members.contacts',  name='invitations_contacts'),
    url(r'^manage_contacts/$', 'muaccounts.views.members.manage_contacts',  name='manage_contacts'),


    #yahoo authentication
    url(r'^bbauth/login/$', 'muaccounts.views.bbauth.login', name="bbauth_login"),
    url(r'^bbauth/success/$', 'muaccounts.views.bbauth.success', name="bbauth_success"),
    url(r'^bbauth/logout/$', 'muaccounts.views.bbauth.logout', name="bbauth.logout"),
    
    url(r'^invitation_request/$', 'muaccounts.views.members.invitation_request', name='invitation_request'),
    url(r'^proceed_invitation_request/(?P<state>invite|reject)/(?P<email>.+)/$', 
        'muaccounts.views.members.change_invitation_request_state', name='proceed_invitation_request'),
    
)
