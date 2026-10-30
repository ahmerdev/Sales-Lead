from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('', views.lead_list_view, name='list'),
    path('add/', views.lead_create_view, name='create'),
    path('import-csv/', views.lead_csv_import_view, name='import_csv'),
    path('find/', views.find_leads_view, name='find_leads'),
    path('seed-samples/', views.seed_sample_leads_view, name='seed_samples'),
    path('<int:pk>/', views.lead_detail_view, name='detail'),
    path('<int:pk>/edit/', views.lead_update_view, name='update'),
    path('<int:pk>/delete/', views.lead_delete_view, name='delete'),
]
