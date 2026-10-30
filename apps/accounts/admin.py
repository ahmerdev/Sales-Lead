from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Workspace, WorkspaceMember, UserSettings

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'full_name', 'role', 'is_staff', 'created_at')
    search_fields = ('email', 'username', 'full_name')
    ordering = ('-created_at',)

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'plan', 'created_at')
    search_fields = ('name', 'slug')

@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ('workspace', 'user', 'role', 'joined_at')


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency_name', 'smtp_host', 'whatsapp_number', 'updated_at')
    exclude = ('smtp_password_enc', 'gemini_api_key_enc')  # secrets are never shown in admin
