from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.kanban_view, name='index'),
    path('kanban/', views.kanban_view, name='kanban'),
    path('lead/<int:lead_id>/stage/', views.update_stage_view, name='update_stage'),
    path('lead/<int:lead_id>/note/', views.add_note_view, name='add_note'),
    path('lead/<int:lead_id>/followup/', views.add_followup_view, name='add_followup'),
    path('followup/<int:followup_id>/complete/', views.complete_followup_view, name='complete_followup'),
]
