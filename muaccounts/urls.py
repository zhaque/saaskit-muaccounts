from django.conf.urls.defaults import *

# to main site urlconf add also:
# (r'^create/$', 'muaccounts.views.create_account'),

urlpatterns = patterns('',
    url(r'^$', 'muaccounts.views.account_detail',
        name='muaccounts_account_detail'),

    url(r'^users/$', 'muaccounts.views.member_list',
        name='muaccounts_member_list'),

    url(r'^remove_member/(?P<user_id>\d+)/$', 'muaccounts.views.remove_member',
        name='muaccounts_remove_member'),

    url(r'^add_member/$', 'muaccounts.views.add_member',
        name='muaccounts_add_member'),

    url(r'^claim/$', 'muaccounts.views.claim_account',
        name='muaccounts_claim_account'),

    url(r'^advanced/$', 'muaccounts.views.advanced_settings',
        name='muaccounts_manage_advanced'),

    url(r'^general/$', 'muaccounts.views.general_settings',
        name='muaccounts_manage_general'),

    url(r'^styles/$', 'muaccounts.views.styles_settings',
        name='muaccounts_manage_styles'),
)
