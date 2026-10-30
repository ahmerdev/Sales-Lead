from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as dj_auth_views
from django.urls import reverse_lazy
from apps.accounts import views as auth_views
from apps.proposals import views as proposal_views
from apps.portfolio import views as portfolio_views
from apps.accounts.forms import UserSMTPPasswordResetForm

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication entry points
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', auth_views.logout_view, name='logout'),

    # Forgot / reset password
    path('password-reset/', dj_auth_views.PasswordResetView.as_view(
        form_class=UserSMTPPasswordResetForm,
        template_name='auth/password_reset_form.html',
        email_template_name='auth/password_reset_email.txt',
        subject_template_name='auth/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('password-reset/sent/', dj_auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', dj_auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('password-reset/complete/', dj_auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

    # Core SaaS Modules
    path('', lambda req: redirect('dashboard:index')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('leads/', include('apps.leads.urls', namespace='leads')),
    path('scanner/', include('apps.scanner.urls', namespace='scanner')),
    path('opportunities/', include('apps.opportunities.urls', namespace='opportunities')),
    path('ai/', include('apps.ai_engine.urls', namespace='ai_engine')),
    path('crm/', include('apps.crm.urls', namespace='crm')),
    path('outreach/', include('apps.outreach.urls', namespace='outreach')),
    path('proposals/', include('apps.proposals.urls', namespace='proposals')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
    path('my-portfolio/', include('apps.portfolio.urls', namespace='portfolio')),

    # Public Interactive Client Proposal Portal
    path('p/<uuid:token>/', proposal_views.public_proposal_view, name='public_proposal'),

    # Public portfolio you share with prospects (no login)
    path('portfolio/<slug:slug>/', portfolio_views.public_portfolio_view, name='public_portfolio'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
