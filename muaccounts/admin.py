from django.contrib import admin

from muaccounts.models import MUAccount, JoinRequest
from muaccounts.forms import MUAccountBaseForm

class MUAccountAdmin(admin.ModelAdmin):
    form=MUAccountBaseForm
admin.site.register(MUAccount, MUAccountAdmin)


class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'muaccount', 'state')

admin.site.register(JoinRequest, JoinRequestAdmin)