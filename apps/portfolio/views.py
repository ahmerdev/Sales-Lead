from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from apps.accounts.models import Workspace
from apps.accounts.services import get_user_settings, public_url, is_local_link, whatsapp_link
from .models import PortfolioItem, PortfolioFAQ, PortfolioTestimonial
from .forms import PortfolioItemForm, PortfolioFAQForm, PortfolioTestimonialForm


def _workspace(request):
    ws_id = request.session.get('active_workspace_id')
    ws = Workspace.objects.filter(id=ws_id, owner=request.user).first() if ws_id else None
    return ws or Workspace.objects.filter(owner=request.user).first() or Workspace.objects.create(
        name=f"{request.user.full_name or request.user.username}'s Agency", owner=request.user)


@login_required
def portfolio_list_view(request):
    ws = _workspace(request)
    items = PortfolioItem.objects.filter(workspace=ws)
    faqs = PortfolioFAQ.objects.filter(workspace=ws)
    testimonials = PortfolioTestimonial.objects.filter(workspace=ws)
    s = get_user_settings(request.user)
    return render(request, 'portfolio/list.html', {
        'items': items,
        'faqs': faqs,
        'testimonials': testimonials,
        'public_link': public_url(request, request.user, reverse('public_portfolio', args=[ws.slug])),
        'portfolio_enabled': s.portfolio_enabled,
        'local_link_warning': is_local_link(request, request.user),
    })


@login_required
def portfolio_create_view(request):
    ws = _workspace(request)
    if request.method == 'POST':
        form = PortfolioItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.workspace = ws
            item.save()
            messages.success(request, f"'{item.title}' added to your portfolio.")
            return redirect('portfolio:list')
    else:
        form = PortfolioItemForm()
    return render(request, 'portfolio/form.html', {'form': form, 'title': 'Add Portfolio Project'})


@login_required
def portfolio_update_view(request, pk):
    item = get_object_or_404(PortfolioItem, pk=pk, workspace__owner=request.user)
    if request.method == 'POST':
        form = PortfolioItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Portfolio project updated.")
            return redirect('portfolio:list')
    else:
        form = PortfolioItemForm(instance=item)
    return render(request, 'portfolio/form.html', {'form': form, 'item': item, 'title': 'Edit Portfolio Project'})


@login_required
def portfolio_delete_view(request, pk):
    item = get_object_or_404(PortfolioItem, pk=pk, workspace__owner=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Portfolio project deleted.")
    return redirect('portfolio:list')


# --- FAQ CRUD ---
@login_required
def faq_create_view(request):
    ws = _workspace(request)
    if request.method == 'POST':
        form = PortfolioFAQForm(request.POST)
        if form.is_valid():
            faq = form.save(commit=False)
            faq.workspace = ws
            faq.save()
            messages.success(request, "FAQ added successfully.")
            return redirect(f"{reverse('accounts:settings')}?tab=faq" if request.GET.get('from') == 'settings' else reverse('portfolio:list'))
    else:
        form = PortfolioFAQForm()
    return render(request, 'portfolio/faq_form.html', {'form': form, 'title': 'Add FAQ Item'})


@login_required
def faq_update_view(request, pk):
    faq = get_object_or_404(PortfolioFAQ, pk=pk, workspace__owner=request.user)
    if request.method == 'POST':
        form = PortfolioFAQForm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
            messages.success(request, "FAQ updated successfully.")
            return redirect(f"{reverse('accounts:settings')}?tab=faq" if request.GET.get('from') == 'settings' else reverse('portfolio:list'))
    else:
        form = PortfolioFAQForm(instance=faq)
    return render(request, 'portfolio/faq_form.html', {'form': form, 'faq': faq, 'title': 'Edit FAQ Item'})


@login_required
def faq_delete_view(request, pk):
    faq = get_object_or_404(PortfolioFAQ, pk=pk, workspace__owner=request.user)
    if request.method == 'POST':
        faq.delete()
        messages.success(request, "FAQ deleted.")
    return redirect(f"{reverse('accounts:settings')}?tab=faq" if request.GET.get('from') == 'settings' else reverse('portfolio:list'))


# --- Testimonial CRUD ---
@login_required
def testimonial_create_view(request):
    ws = _workspace(request)
    if request.method == 'POST':
        form = PortfolioTestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.workspace = ws
            testimonial.save()
            messages.success(request, "Client Testimonial added successfully.")
            return redirect(f"{reverse('accounts:settings')}?tab=faq" if request.GET.get('from') == 'settings' else reverse('portfolio:list'))
    else:
        form = PortfolioTestimonialForm()
    return render(request, 'portfolio/testimonial_form.html', {'form': form, 'title': 'Add Client Testimonial'})


@login_required
def testimonial_update_view(request, pk):
    testimonial = get_object_or_404(PortfolioTestimonial, pk=pk, workspace__owner=request.user)
    if request.method == 'POST':
        form = PortfolioTestimonialForm(request.POST, instance=testimonial)
        if form.is_valid():
            form.save()
            messages.success(request, "Testimonial updated successfully.")
            return redirect(f"{reverse('accounts:settings')}?tab=faq" if request.GET.get('from') == 'settings' else reverse('portfolio:list'))
    else:
        form = PortfolioTestimonialForm(instance=testimonial)
    return render(request, 'portfolio/testimonial_form.html', {'form': form, 'testimonial': testimonial, 'title': 'Edit Testimonial'})


@login_required
def testimonial_delete_view(request, pk):
    testimonial = get_object_or_404(PortfolioTestimonial, pk=pk, workspace__owner=request.user)
    if request.method == 'POST':
        testimonial.delete()
        messages.success(request, "Testimonial deleted.")
    return redirect(f"{reverse('accounts:settings')}?tab=faq" if request.GET.get('from') == 'settings' else reverse('portfolio:list'))


def public_portfolio_view(request, slug):
    """Public page a prospect opens from your email / WhatsApp / proposal. No login needed."""
    workspace = get_object_or_404(Workspace, slug=slug)
    owner = workspace.owner
    s = get_user_settings(owner)
    if not s.portfolio_enabled:
        raise Http404("This portfolio is not available.")

    items = list(workspace.portfolio_items.filter(is_published=True))
    faqs = list(workspace.faqs.filter(is_published=True))
    testimonials = list(workspace.testimonials.filter(is_published=True))
    if not testimonials:
        testimonials = [i for i in items if i.testimonial]

    from apps.proposals.models import PortfolioProject
    portfolio_projects = list(PortfolioProject.objects.filter(user=owner))

    contact_email = s.reply_to or owner.email
    whatsapp = whatsapp_link(
        s.whatsapp_number,
        f"Hi {s.display_agency_name}, I saw your portfolio and would like to talk about a project.",
    )
    return render(request, 'portfolio/public.html', {
        'workspace': workspace,
        'owner': owner,
        'agency': s,
        'items': items,
        'faqs': faqs,
        'testimonials': testimonials,
        'portfolio_projects': portfolio_projects,
        'industries': sorted({i.industry for i in items if i.industry}),
        'contact_email': contact_email,
        'whatsapp_url': whatsapp,
    })

