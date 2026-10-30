from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from apps.leads.models import Lead
from .models import CRMActivity, FollowUp

@login_required
def kanban_view(request):
    workspace_owner = request.user
    leads = Lead.objects.filter(workspace__owner=workspace_owner)

    columns = {
        'NEW': leads.filter(status='NEW'),
        'CONTACTED': leads.filter(status='CONTACTED'),
        'INTERESTED': leads.filter(status='INTERESTED'),
        'PROPOSAL': leads.filter(status='PROPOSAL'),
        'WON': leads.filter(status='WON'),
    }

    counts = {key: val.count() for key, val in columns.items()}

    context = {
        'columns': columns,
        'counts': counts,
    }
    return render(request, 'crm/kanban.html', context)


@login_required
def update_stage_view(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)
    new_status = request.POST.get('status') or request.GET.get('status')

    valid_statuses = [choice[0] for choice in Lead.STATUS_CHOICES]
    if new_status in valid_statuses:
        old_status = lead.get_status_display()
        lead.status = new_status
        lead.save(update_fields=['status'])

        # Log activity
        CRMActivity.objects.create(
            lead=lead,
            user=request.user,
            activity_type='STATUS_CHANGE',
            description=f"Moved stage from {old_status} to {lead.get_status_display()}"
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({'success': True, 'lead_id': lead.id, 'status': new_status})

        messages.success(request, f"{lead.business_name} moved to {lead.get_status_display()}!")
    
    # Redirect back to where it came from
    referrer = request.META.get('HTTP_REFERER', '')
    if 'kanban' in referrer:
        return redirect('crm:kanban')
    return redirect('leads:detail', pk=lead.id)


@login_required
def add_note_view(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)
    if request.method == 'POST':
        note_text = request.POST.get('note', '').strip()
        if note_text:
            CRMActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='NOTE',
                description=note_text
            )
            messages.success(request, "Note added to lead timeline.")
    return redirect('leads:detail', pk=lead.id)


@login_required
def add_followup_view(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)
    if request.method == 'POST':
        date_str = request.POST.get('scheduled_date')
        notes = request.POST.get('notes', '').strip()
        if date_str:
            FollowUp.objects.create(
                lead=lead,
                scheduled_date=date_str,
                notes=notes or "Follow-up discussion"
            )
            messages.success(request, f"Follow-up scheduled for {date_str}!")
    return redirect('leads:detail', pk=lead.id)


@login_required
def complete_followup_view(request, followup_id):
    followup = get_object_or_404(FollowUp, id=followup_id, lead__workspace__owner=request.user)
    followup.mark_as_completed()
    messages.success(request, f"Follow-up for {followup.lead.business_name} marked as complete!")
    return redirect('leads:detail', pk=followup.lead.id)
