from django.contrib import admin

from muaccounts.models import MUAccount, InvitationRequest
from muaccounts.forms import MUAccountBaseForm

class MUAccountAdmin(admin.ModelAdmin):
    form=MUAccountBaseForm
admin.site.register(MUAccount, MUAccountAdmin)


class InvitationRequestAdmin(admin.ModelAdmin):
    list_display = ('email', 'muaccount', 'state')
admin.site.register(InvitationRequest, InvitationRequestAdmin)
