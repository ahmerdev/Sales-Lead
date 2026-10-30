from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('', views.opportunities_overview_view, name='index'),
    path('list/', views.opportunities_overview_view, name='list'),
]
