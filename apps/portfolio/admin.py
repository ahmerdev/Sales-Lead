from django.contrib import admin
from .models import PortfolioItem


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'workspace', 'industry', 'is_published', 'sort_order', 'created_at')
    list_filter = ('is_published', 'industry')
