from django.contrib import admin
from .models import Campaign, CampaignLead

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry_target', 'status', 'created_at')

@admin.register(CampaignLead)
class CampaignLeadAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'lead', 'status', 'sent_at')
