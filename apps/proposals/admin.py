from django.contrib import admin
from .models import Proposal

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('title', 'client_name', 'investment_amount', 'currency', 'status', 'created_at')
    list_filter = ('status',)
