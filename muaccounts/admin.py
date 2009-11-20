from django.contrib import admin

from muaccounts.models import MUAccount
from muaccounts.forms import MUAccountBaseForm

class MUAccountAdmin(admin.ModelAdmin):
    form=MUAccountBaseForm
admin.site.register(MUAccount, MUAccountAdmin)
