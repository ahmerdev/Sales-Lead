from django.contrib import admin
from .models import Lead, LeadContact

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'industry', 'city', 'opportunity_score', 'opportunity_level', 'status', 'source')
    list_filter = ('industry', 'status', 'opportunity_level', 'source')
    search_fields = ('business_name', 'email', 'city', 'website')

@admin.register(LeadContact)
class LeadContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'lead', 'title', 'email', 'phone', 'is_primary')
