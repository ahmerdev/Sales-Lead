from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.portfolio_list_view, name='list'),
    path('add/', views.portfolio_create_view, name='create'),
    path('<int:pk>/edit/', views.portfolio_update_view, name='update'),
    path('<int:pk>/delete/', views.portfolio_delete_view, name='delete'),

    # FAQs
    path('faqs/add/', views.faq_create_view, name='faq_create'),
    path('faqs/<int:pk>/edit/', views.faq_update_view, name='faq_update'),
    path('faqs/<int:pk>/delete/', views.faq_delete_view, name='faq_delete'),

    # Testimonials
    path('testimonials/add/', views.testimonial_create_view, name='testimonial_create'),
    path('testimonials/<int:pk>/edit/', views.testimonial_update_view, name='testimonial_update'),
    path('testimonials/<int:pk>/delete/', views.testimonial_delete_view, name='testimonial_delete'),
]

