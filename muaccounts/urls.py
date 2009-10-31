from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
# to main site urlconf add also:
# (r'^create/$', 'muaccounts.views.create_account'),

urlpatterns = patterns('',
    url(r'^$', 'muaccounts.views.account_detail',
        name='muaccounts_account_detail'),

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
    url(r'^invite/$', 'muaccounts.views.members.invite', name="muaccounts_add_member"),
    
    url(r'^accept/(\w+)/$', 'muaccounts.views.members.accept_join', name='friends_accept_join'),
    
    url(r'^contacts/$', 'muaccounts.views.members.contacts',  name='invitations_contacts'),
    #google authentication
    url(r'^authsub_login/$', 'muaccounts.views.authsub_login', name="authsub_login"),
    #yahoo authentication
    url(r'^bbauth/login/$', 'muaccounts.views.bbauth.login', name="bbauth_login"),
    url(r'^bbauth/success/$', 'muaccounts.views.bbauth.success', name="bbauth_success"),
    url(r'^bbauth/logout/$', 'muaccounts.views.bbauth.logout', name="bbauth.logout"),
    
    
)
