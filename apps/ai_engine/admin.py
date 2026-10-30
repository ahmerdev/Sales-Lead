from django.contrib import admin
from .models import AIPitch

@admin.register(AIPitch)
class AIPitchAdmin(admin.ModelAdmin):
    list_display = ('lead', 'subject', 'status', 'created_at')
    list_filter = ('status',)
