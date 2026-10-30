from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from apps.leads.models import Lead
from apps.proposals.models import Proposal

@login_required
def reports_dashboard_view(request):
    workspace_owner = request.user
    leads = Lead.objects.filter(workspace__owner=workspace_owner)

    total_leads = leads.count()
    high_opps = leads.filter(opportunity_level='HIGH').count()
    won_leads = leads.filter(status='WON').count()

    # Industry Breakdown
    industry_data = leads.values('industry').annotate(count=Count('id')).order_by('-count')

    # Status Pipeline Funnel
    pipeline_data = {
        'NEW': leads.filter(status='NEW').count(),
        'CONTACTED': leads.filter(status='CONTACTED').count(),
        'REPLIED': leads.filter(status='REPLIED').count(),
        'INTERESTED': leads.filter(status='INTERESTED').count(),
        'PROPOSAL': leads.filter(status='PROPOSAL').count(),
        'WON': leads.filter(status='WON').count(),
    }

    # Revenue metrics
    proposals = Proposal.objects.filter(lead__workspace__owner=workspace_owner)
    pipeline_value = proposals.aggregate(total=Sum('investment_amount'))['total'] or 0
    won_value = proposals.filter(status='ACCEPTED').aggregate(total=Sum('investment_amount'))['total'] or 0

    context = {
        'total_leads': total_leads,
        'high_opps': high_opps,
        'won_leads': won_leads,
        'industry_data': industry_data,
        'pipeline_data': pipeline_data,
        'pipeline_value': pipeline_value,
        'won_value': won_value,
    }
    return render(request, 'reports/index.html', context)
