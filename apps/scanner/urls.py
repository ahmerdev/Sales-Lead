from django.urls import path
from . import views

app_name = 'scanner'

urlpatterns = [
    path('', views.scanner_dashboard_view, name='index'),
    path('scan/<int:lead_id>/', views.scan_lead_view, name='scan_lead'),
]
