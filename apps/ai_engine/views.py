from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.leads.models import Lead
from .models import AIPitch
from .services import generate_ai_outreach_pitch

@login_required
def generate_pitch_view(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)
    sender = request.user.full_name or request.user.username
    pitch = generate_ai_outreach_pitch(lead, sender_name=sender, user=request.user)
    
    messages.success(request, f"🚀 Personalized AI Cold Outreach pitch generated for {lead.business_name}!")
    return redirect('leads:detail', pk=lead.id)


@login_required
def approve_pitch_view(request, pitch_id):
    pitch = get_object_or_404(AIPitch, id=pitch_id, lead__workspace__owner=request.user)
    pitch.status = 'APPROVED'
    pitch.save()

    # Update lead status to CONTACTED if it was NEW
    if pitch.lead.status == 'NEW':
        pitch.lead.status = 'CONTACTED'
        pitch.lead.save(update_fields=['status'])

    messages.success(request, f"Pitch approved for {pitch.lead.business_name}!")
    return redirect('leads:detail', pk=pitch.lead.id)


@login_required
def ai_pitches_list_view(request):
    pitches = AIPitch.objects.filter(lead__workspace__owner=request.user).order_by('-created_at')
    return render(request, 'outreach/pitches_list.html', {'pitches': pitches})
