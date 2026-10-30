from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    path('', views.proposals_list_view, name='list'),
    path('lead/<int:lead_id>/create/', views.create_proposal_for_lead, name='create'),
    path('<int:pk>/', views.proposal_detail_view, name='detail'),
    path('<int:pk>/send-email/', views.send_proposal_email_view, name='send_email'),
    path('<int:pk>/send-whatsapp/', views.send_proposal_whatsapp_view, name='send_whatsapp'),
    path('<int:pk>/cancel/', views.cancel_proposal_view, name='cancel'),
    path('<int:pk>/delete/', views.delete_proposal_view, name='delete'),
]
