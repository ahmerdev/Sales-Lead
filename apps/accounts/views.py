from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import User, Workspace, WorkspaceMember, UserSettings
from django.contrib.auth import update_session_auth_hash
from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm, EmailSettingsForm, WhatsAppSettingsForm,
    ApiSettingsForm, AgencySettingsForm, StyledPasswordChangeForm,
)
from .services import get_user_settings, send_user_email, MailerError, portfolio_link, public_url, is_local_link

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # User is created as unapproved by default! Super Admin must approve.
            user = User.objects.create_user(
                username=username,
                email=email,
                password=form.cleaned_data['password'],
                full_name=form.cleaned_data['full_name'],
                role='admin',
                is_approved=False
            )

            # Create default workspace
            workspace_name = f"{user.full_name or username}'s Agency"
            workspace = Workspace.objects.create(
                name=workspace_name,
                owner=user,
                plan='pro'
            )
            WorkspaceMember.objects.create(workspace=workspace, user=user, role='owner')
            UserSettings.objects.create(user=user)

            return render(request, 'auth/approval_pending.html', {
                'full_name': user.full_name or username,
                'email': user.email
            })
    else:
        form = UserRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            password = form.cleaned_data['password']

            user_obj = User.objects.filter(email__iexact=email).first()
            if user_obj:
                user = authenticate(request, username=user_obj.email, password=password)
                if user is not None:
                    # Super admin check vs unapproved user check
                    if not user.is_superuser and not getattr(user, 'is_approved', False):
                        messages.warning(
                            request,
                            "Approval Pending: Aapka account create ho chuka hai lekin abhi Super Admin ki taraf se Approve hona baqi hai. "
                            "Super Admin ke Approve karne ke baad aap access kar sakenge."
                        )
                        return render(request, 'auth/login.html', {'form': form, 'pending_approval': True})

                    login(request, user)
                    messages.success(request, f"Welcome back, {user.full_name or user.username}!")
                    return redirect('dashboard:index')

            messages.error(request, "Invalid email or password.")
    else:
        form = UserLoginForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def profile_view(request):
    # Profile now lives inside the Settings page.
    return redirect(f"{reverse('accounts:settings')}?tab=profile")


from apps.portfolio.models import PortfolioFAQ, PortfolioTestimonial

SETTINGS_TABS = ('profile', 'email', 'whatsapp', 'api', 'agency', 'faq', 'security')



@login_required
def settings_view(request):
    user = request.user
    s = get_user_settings(user)
    workspace = Workspace.objects.filter(owner=user).first()
    tab = request.GET.get('tab') or request.POST.get('tab') or 'profile'
    if tab not in SETTINGS_TABS:
        tab = 'profile'

    forms_by_tab = {
        'profile': UserProfileForm(instance=user),
        'email': EmailSettingsForm(instance=s),
        'whatsapp': WhatsAppSettingsForm(instance=s),
        'api': ApiSettingsForm(),
        'agency': AgencySettingsForm(instance=s),
        'security': StyledPasswordChangeForm(user),
    }

    if request.method == 'POST':
        section = request.POST.get('section', tab)
        if section not in SETTINGS_TABS:
            section = 'profile'
        tab = section

        if section == 'profile':
            form = UserProfileForm(request.POST, instance=user)
        elif section == 'email':
            form = EmailSettingsForm(request.POST, instance=s)
        elif section == 'whatsapp':
            form = WhatsAppSettingsForm(request.POST, instance=s)
        elif section == 'api':
            form = ApiSettingsForm(request.POST)
        elif section == 'agency':
            form = AgencySettingsForm(request.POST, request.FILES, instance=s)
        else:
            form = StyledPasswordChangeForm(user, request.POST)

        if form.is_valid():
            if section == 'api':
                if form.cleaned_data.get('clear_gemini'):
                    s.gemini_api_key = ''
                    messages.success(request, "Your Gemini API key was removed.")
                elif form.cleaned_data.get('gemini_api_key'):
                    s.gemini_api_key = form.cleaned_data['gemini_api_key'].strip()
                    messages.success(request, "Gemini API key saved. AI pitches will now use your key.")
                else:
                    messages.info(request, "Nothing changed.")
                s.save()
            elif section == 'security':
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully.")
            else:
                form.save()
                messages.success(request, "Settings saved.")

            if section == 'email' and 'send_test' in request.POST:
                try:
                    send_user_email(
                        request.user, request.user.email,
                        "Test email from LeadRadar AI",
                        "Great news: your mailbox is connected. Pitches and proposals you send from LeadRadar "
                        "will now go out from this address.",
                    )
                    messages.success(request, f"Test email sent to {request.user.email}. Check your inbox.")
                except MailerError as exc:
                    messages.error(request, str(exc))
            return redirect(f"{request.path}?tab={section}")

        forms_by_tab[section] = form

    context = {
        'tab': tab,
        'profile_form': forms_by_tab['profile'],
        'email_form': forms_by_tab['email'],
        'whatsapp_form': forms_by_tab['whatsapp'],
        'api_form': forms_by_tab['api'],
        'agency_form': forms_by_tab['agency'],
        'security_form': forms_by_tab['security'],
        'settings_obj': s,
        'workspace': workspace,
        'faqs': PortfolioFAQ.objects.filter(workspace=workspace) if workspace else [],
        'testimonials': PortfolioTestimonial.objects.filter(workspace=workspace) if workspace else [],
        'portfolio_url': public_url(request, user, reverse('public_portfolio', args=[workspace.slug])) if workspace else '',
        'local_link_warning': is_local_link(request, user),
    }
    return render(request, 'auth/settings.html', context)


@login_required
def switch_workspace_view(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    if workspace.owner == request.user or WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
        request.session['active_workspace_id'] = workspace.id
        messages.success(request, f"Switched workspace to {workspace.name}")
    else:
        messages.error(request, "You do not have access to that workspace.")
    return redirect('dashboard:index')


# ==========================================
# 👑 SUPER ADMIN MANAGEMENT PANEL & APPROVALS
# ==========================================

from apps.leads.models import Lead
from apps.scanner.models import WebsiteAudit
from apps.proposals.models import Proposal
from .forms import SuperAdminCreateUserForm

def super_admin_required(view_func):
    """Decorator to restrict access strictly to Super Admin."""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, "Access Denied: Only Super Administrators can access the User Management panel.")
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return _wrapped


@super_admin_required
def super_admin_dashboard_view(request):
    all_users = User.objects.all().order_by('-date_joined')
    
    # Platform totals
    total_users_count = all_users.count()
    pending_approvals_count = all_users.filter(is_approved=False, is_superuser=False).count()
    total_leads_count = Lead.objects.count()
    total_audits_count = WebsiteAudit.objects.count()
    total_proposals_count = Proposal.objects.count()
    total_deals_won_count = Lead.objects.filter(status='WON').count()

    # Detailed work stats for each user
    user_stats = []
    for u in all_users:
        user_leads = Lead.objects.filter(workspace__owner=u).count()
        user_audits = WebsiteAudit.objects.filter(lead__workspace__owner=u).count()
        user_proposals = Proposal.objects.filter(lead__workspace__owner=u).count()
        user_won = Lead.objects.filter(workspace__owner=u, status='WON').count()
        ws = u.owned_workspaces.first()

        user_stats.append({
            'user': u,
            'workspace': ws,
            'leads_count': user_leads,
            'audits_count': user_audits,
            'proposals_count': user_proposals,
            'won_count': user_won,
        })

    create_form = SuperAdminCreateUserForm()

    context = {
        'user_stats': user_stats,
        'total_users': total_users_count,
        'pending_approvals': pending_approvals_count,
        'total_leads': total_leads_count,
        'total_audits': total_audits_count,
        'total_proposals': total_proposals_count,
        'total_won': total_deals_won_count,
        'create_form': create_form,
    }
    return render(request, 'auth/super_admin.html', context)


@super_admin_required
def super_admin_approve_user_view(request, user_id):
    target = get_object_or_404(User, id=user_id)
    target.is_approved = True
    target.save(update_fields=['is_approved'])
    messages.success(request, f"User {target.email} ({target.full_name or target.username}) has been APPROVED! They can now log in.")
    return redirect('accounts:super_admin')


@super_admin_required
def super_admin_reject_user_view(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        messages.error(request, "You cannot suspend your own superuser account.")
        return redirect('accounts:super_admin')
    target.is_approved = False
    target.save(update_fields=['is_approved'])
    messages.warning(request, f"User {target.email} access has been SUSPENDED / UNAPPROVED.")
    return redirect('accounts:super_admin')


@super_admin_required
def super_admin_toggle_admin_view(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        messages.error(request, "You cannot remove your own Super Admin status.")
        return redirect('accounts:super_admin')
    target.is_superuser = not target.is_superuser
    target.is_staff = target.is_superuser
    target.save(update_fields=['is_superuser', 'is_staff'])
    status_str = "granted Super Admin" if target.is_superuser else "revoked Super Admin"
    messages.success(request, f"User {target.email} has been {status_str}.")
    return redirect('accounts:super_admin')


@super_admin_required
def super_admin_delete_user_view(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('accounts:super_admin')
    email = target.email
    target.delete()
    messages.success(request, f"User {email} and associated data were removed.")
    return redirect('accounts:super_admin')


@super_admin_required
def super_admin_create_user_view(request):
    if request.method == 'POST':
        form = SuperAdminCreateUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            is_appr = form.cleaned_data['is_approved']
            is_super = form.cleaned_data['is_superuser']

            user = User.objects.create_user(
                username=username,
                email=email,
                password=form.cleaned_data['password'],
                full_name=form.cleaned_data['full_name'],
                role=form.cleaned_data['role'],
                is_approved=is_appr,
                is_superuser=is_super,
                is_staff=is_super
            )

            # Create default workspace
            workspace_name = f"{user.full_name or username}'s Agency"
            workspace = Workspace.objects.create(name=workspace_name, owner=user, plan='pro')
            WorkspaceMember.objects.create(workspace=workspace, user=user, role='owner')
            UserSettings.objects.create(user=user)

            messages.success(request, f"New user {user.email} successfully created! (Approved: {is_appr})")
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f"{field.title()}: {e}")
    return redirect('accounts:super_admin')

