from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.leads.models import Lead
from apps.scanner.models import WebsiteAudit
from apps.scanner.services import scan_lead_website

@login_required
def scan_lead_view(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)
    audit = scan_lead_website(lead)
    
    messages.success(
        request, 
        f"🎯 Website Audit completed for {lead.business_name}! Opportunity Score: {lead.opportunity_score}/100 ({lead.opportunity_level})"
    )
    return redirect('leads:detail', pk=lead.id)


@login_required
def scanner_dashboard_view(request):
    audits = WebsiteAudit.objects.filter(lead__workspace__owner=request.user).order_by('-scanned_at')[:30]
    return render(request, 'scanner/audit.html', {'audits': audits})
