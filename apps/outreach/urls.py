from django.urls import path
from . import views

app_name = 'outreach'

urlpatterns = [
    path('', views.campaigns_list_view, name='campaigns'),
    path('inbox/', views.communications_inbox_view, name='inbox'),
    path('new/', views.campaign_create_view, name='create_campaign'),
    path('<int:pk>/', views.campaign_detail_view, name='detail'),
    path('<int:campaign_id>/sent/<int:lead_id>/', views.mark_campaign_lead_sent_view, name='mark_sent'),

    # Direct messaging & Inbound reply tracking
    path('lead/<int:lead_id>/send-email/', views.send_direct_email_view, name='send_email'),
    path('lead/<int:lead_id>/send-whatsapp/', views.send_direct_whatsapp_view, name='send_whatsapp'),
    path('lead/<int:lead_id>/log-reply/', views.log_inbound_reply_view, name='log_reply'),

    # Email Templates Builder
    path('templates/', views.email_templates_list_view, name='templates_list'),
    path('templates/new/', views.email_template_create_view, name='template_create'),
    path('templates/<int:pk>/edit/', views.email_template_edit_view, name='template_edit'),
    path('templates/<int:pk>/delete/', views.email_template_delete_view, name='template_delete'),
    path('templates/api/parse/<int:template_id>/<int:lead_id>/', views.email_template_parse_api, name='template_parse_api'),
]
