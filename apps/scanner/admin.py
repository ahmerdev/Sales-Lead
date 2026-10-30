from django.contrib import admin
from .models import WebsiteAudit

@admin.register(WebsiteAudit)
class WebsiteAuditAdmin(admin.ModelAdmin):
    list_display = ('lead', 'scanned_url', 'is_ssl', 'has_whatsapp_cta', 'has_online_booking', 'has_online_ordering', 'scanned_at')
