from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('workspace/switch/<int:workspace_id>/', views.switch_workspace_view, name='switch_workspace'),

    # Super Admin Control
    path('super-admin/', views.super_admin_dashboard_view, name='super_admin'),
    path('super-admin/approve/<int:user_id>/', views.super_admin_approve_user_view, name='super_admin_approve'),
    path('super-admin/reject/<int:user_id>/', views.super_admin_reject_user_view, name='super_admin_reject'),
    path('super-admin/toggle-admin/<int:user_id>/', views.super_admin_toggle_admin_view, name='super_admin_toggle_admin'),
    path('super-admin/delete/<int:user_id>/', views.super_admin_delete_user_view, name='super_admin_delete'),
    path('super-admin/create-user/', views.super_admin_create_user_view, name='super_admin_create_user'),
]
