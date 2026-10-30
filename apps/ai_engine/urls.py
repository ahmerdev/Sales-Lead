from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('generate/<int:lead_id>/', views.generate_pitch_view, name='generate_pitch'),
    path('approve/<int:pitch_id>/', views.approve_pitch_view, name='approve_pitch'),
    path('pitches/', views.ai_pitches_list_view, name='pitches_list'),
]
