from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Lead
from .forms import LeadForm, LeadCSVImportForm
from .services import import_leads_from_csv
from .discovery import discover_real_leads, DiscoveryError
from apps.accounts.services import get_user_settings, portfolio_link

def get_user_workspace(request):
    from apps.accounts.models import Workspace
    ws_id = request.session.get('active_workspace_id')
    if ws_id:
        ws = Workspace.objects.filter(id=ws_id, owner=request.user).first()
        if ws:
            return ws
    ws = Workspace.objects.filter(owner=request.user).first()
    if not ws:
        ws = Workspace.objects.create(name=f"{request.user.username}'s Agency", owner=request.user)
    request.session['active_workspace_id'] = ws.id
    return ws


@login_required
def lead_list_view(request):
    workspace = get_user_workspace(request)
    queryset = Lead.objects.filter(workspace=workspace)

    # Filters
    search_query = request.GET.get('q', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(business_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    industry = request.GET.get('industry', '')
    if industry:
        queryset = queryset.filter(industry=industry)

    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)

    live = request.GET.get('live', '')
    if live == 'yes':
        queryset = queryset.filter(is_website_live=True)
    elif live == 'no':
        queryset = queryset.filter(is_website_live=False)
    elif live == 'unchecked':
        queryset = queryset.filter(is_website_live__isnull=True)

    level = request.GET.get('level', '')
    if level:
        queryset = queryset.filter(opportunity_level=level)

    # Statistics for filter bar
    total_leads = Lead.objects.filter(workspace=workspace).count()
    high_opps = Lead.objects.filter(workspace=workspace, opportunity_level='HIGH').count()

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'leads': page_obj,
        'industries': Lead.INDUSTRY_CHOICES,
        'statuses': Lead.STATUS_CHOICES,
        'levels': Lead.OPPORTUNITY_LEVEL_CHOICES,
        'selected_industry': industry,
        'selected_status': status,
        'selected_level': level,
        'selected_live': live,
        'search_query': search_query,
        'total_count': total_leads,
        'high_count': high_opps,
    }
    return render(request, 'leads/list.html', context)


@login_required
def lead_detail_view(request, pk):
    workspace = get_user_workspace(request)
    lead = get_object_or_404(Lead, id=pk, workspace=workspace)

    # Fetch related audit, opportunities, AI pitches, CRM notes
    audit = getattr(lead, 'audit', None)
    opportunities = lead.opportunities.all()
    ai_pitches = lead.ai_pitches.all().order_by('-created_at')
    activities = lead.crm_activities.all().order_by('-created_at')
    followups = lead.followups.all().order_by('scheduled_date')
    lead_messages = lead.messages.all().order_by('created_at')
    latest_pitch = ai_pitches.first()

    from apps.outreach.models import EmailTemplate
    email_templates = EmailTemplate.objects.filter(user=request.user).order_by('-is_default', 'name')

    context = {
        'lead': lead,
        'audit': audit,
        'opportunities': opportunities,
        'ai_pitches': ai_pitches,
        'latest_pitch': latest_pitch,
        'activities': activities,
        'followups': followups,
        'lead_messages': lead_messages,
        'email_templates': email_templates,
        'email_ready': get_user_settings(request.user).smtp_ready,
        'portfolio_ready': bool(portfolio_link(request, request.user, workspace)),
    }
    return render(request, 'leads/detail.html', context)


@login_required
def lead_create_view(request):
    workspace = get_user_workspace(request)
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.workspace = workspace
            lead.source = 'MANUAL'
            lead.save()
            messages.success(request, f"Lead '{lead.business_name}' added successfully!")
            return redirect('leads:detail', pk=lead.pk)
    else:
        form = LeadForm()

    return render(request, 'leads/form.html', {'form': form, 'title': 'Add New Lead'})


@login_required
def lead_update_view(request, pk):
    workspace = get_user_workspace(request)
    lead = get_object_or_404(Lead, id=pk, workspace=workspace)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lead '{lead.business_name}' updated successfully.")
            return redirect('leads:detail', pk=lead.pk)
    else:
        form = LeadForm(instance=lead)

    return render(request, 'leads/form.html', {'form': form, 'lead': lead, 'title': 'Edit Lead'})


@login_required
def lead_delete_view(request, pk):
    workspace = get_user_workspace(request)
    lead = get_object_or_404(Lead, id=pk, workspace=workspace)
    if request.method == 'POST':
        name = lead.business_name
        lead.delete()
        messages.success(request, f"Lead '{name}' deleted.")
        return redirect('leads:list')
    return render(request, 'leads/confirm_delete.html', {'lead': lead})


@login_required
def lead_csv_import_view(request):
    workspace = get_user_workspace(request)
    if request.method == 'POST':
        form = LeadCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            created, errors = import_leads_from_csv(csv_file, workspace)
            if created > 0:
                messages.success(request, f"Successfully imported {created} leads from CSV!")
                if errors:
                    messages.warning(request, f"Encountered {len(errors)} warnings during import.")
                return redirect('leads:list')
            else:
                messages.error(request, "No leads were imported. Please check CSV formatting.")
    else:
        form = LeadCSVImportForm()

    return render(request, 'leads/import_csv.html', {'form': form})


@login_required
def find_leads_view(request):
    workspace = get_user_workspace(request)
    if request.method == 'POST':
        industry = request.POST.get('industry', 'Restaurant')
        country = request.POST.get('country', 'United Arab Emirates')
        city = request.POST.get('city', 'Dubai')
        count = request.POST.get('count', 10)

        try:
            result = discover_real_leads(workspace, industry, country, city, count)
        except DiscoveryError as exc:
            messages.error(request, str(exc))
            return redirect('leads:find_leads')

        created = len(result['created'])
        if created:
            messages.success(
                request,
                f"Successfully discovered and saved {created} real, live {industry} businesses in {city}, {country} with verified websites!"
            )
            return redirect('leads:list')

        if result.get('duplicates', 0) > 0:
            messages.info(
                request,
                f"Found {result['duplicates']} active {industry} businesses in {city}, but they are already in your Leads directory."
            )
            return redirect('leads:list')

        messages.warning(
            request,
            f"No new live {industry} businesses could be found in {city}. "
            f"Try selecting another nearby city or another industry."
        )
        return redirect('leads:find_leads')

    return render(request, 'leads/find_leads.html', {
        'industries': Lead.INDUSTRY_CHOICES,
    })


@login_required
def seed_sample_leads_view(request):
    workspace = get_user_workspace(request)
    samples = [
        {
            'business_name': 'ABC Restaurant & Grill',
            'website': 'https://abcrestaurant.com',
            'email': 'orders@abcrestaurant.com',
            'phone': '+971 4 332 1199',
            'city': 'Dubai',
            'country': 'United Arab Emirates',
            'industry': 'Restaurant',
            'status': 'NEW',
        },
        {
            'business_name': 'XYZ Dental & Implant Clinic',
            'website': 'https://xyzdentalclinic.ae',
            'email': 'appointments@xyzdentalclinic.ae',
            'phone': '+971 4 456 7890',
            'city': 'Dubai',
            'country': 'United Arab Emirates',
            'industry': 'Dental',
            'status': 'CONTACTED',
        },
        {
            'business_name': 'Dubai Fitness & CrossFit Arena',
            'website': 'https://dubaifitnessarena.com',
            'email': 'membership@dubaifitnessarena.com',
            'phone': '+971 50 882 3451',
            'city': 'Dubai',
            'country': 'United Arab Emirates',
            'industry': 'Fitness',
            'status': 'INTERESTED',
        },
        {
            'business_name': 'Skyline Luxury Real Estate',
            'website': 'https://skylinedubaiproperties.com',
            'email': 'invest@skylinedubaiproperties.com',
            'phone': '+971 4 220 9000',
            'city': 'Dubai',
            'country': 'United Arab Emirates',
            'industry': 'Real Estate',
            'status': 'PROPOSAL',
        },
        {
            'business_name': 'Gulf Home Care & Repairs',
            'website': 'https://gulfhomecare.ae',
            'email': 'help@gulfhomecare.ae',
            'phone': '+971 55 911 2233',
            'city': 'Abu Dhabi',
            'country': 'United Arab Emirates',
            'industry': 'Home Services',
            'status': 'NEW',
        }
    ]

    for item in samples:
        if not Lead.objects.filter(workspace=workspace, business_name=item['business_name']).exists():
            Lead.objects.create(workspace=workspace, source='DISCOVERY', **item)

    messages.success(request, "Loaded starter sample leads from blueprint (ABC Restaurant, XYZ Dental, Dubai Fitness, etc.)!")
    return redirect('leads:list')
