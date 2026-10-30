from django.contrib import admin
from .models import OpportunityItem

@admin.register(OpportunityItem)
class OpportunityItemAdmin(admin.ModelAdmin):
    list_display = ('lead', 'title', 'score_impact', 'category', 'recommended_service')
    list_filter = ('category',)
