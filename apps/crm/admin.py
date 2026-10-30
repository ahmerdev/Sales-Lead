from django.contrib import admin
from .models import CRMActivity, FollowUp

@admin.register(CRMActivity)
class CRMActivityAdmin(admin.ModelAdmin):
    list_display = ('lead', 'activity_type', 'created_at')
    list_filter = ('activity_type',)

@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('lead', 'scheduled_date', 'is_completed')
    list_filter = ('is_completed',)
