import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from apps.leads.models import Lead
from apps.ai_engine.models import AIPitch
from apps.ai_engine.services import generate_ai_outreach_pitch
from apps.crm.models import CRMActivity
from apps.accounts.services import (
    get_user_settings, send_user_email, compose_message, MailerError,
    portfolio_link, is_local_link, clean_whatsapp_number,
)
from .models import Campaign, CampaignLead, LeadMessage

@login_required
def campaigns_list_view(request):
    campaigns = Campaign.objects.filter(workspace__owner=request.user).order_by('-created_at')
    
    if not campaigns.exists():
        ws = request.user.owned_workspaces.first()
        if ws:
            sample_camp = Campaign.objects.create(
                workspace=ws,
                name="Dubai High-Opportunity Outreach",
                industry_target="Restaurant",
                status="ACTIVE"
            )
            for lead in Lead.objects.filter(workspace=ws)[:5]:
                CampaignLead.objects.get_or_create(campaign=sample_camp, lead=lead)
            campaigns = Campaign.objects.filter(workspace__owner=request.user)

    return render(request, 'outreach/campaigns.html', {'campaigns': campaigns})


@login_required
def campaign_detail_view(request, pk):
    campaign = get_object_or_404(Campaign, id=pk, workspace__owner=request.user)
    camp_leads = campaign.campaign_leads.select_related('lead', 'pitch').all()

    context = {
        'campaign': campaign,
        'campaign_leads': camp_leads,
    }
    return render(request, 'outreach/campaign_detail.html', context)


@login_required
def campaign_create_view(request):
    ws = request.user.owned_workspaces.first()
    if request.method == 'POST':
        name = request.POST.get('name', 'New Outreach Campaign')
        industry = request.POST.get('industry', 'Restaurant')

        camp = Campaign.objects.create(
            workspace=ws,
            name=name,
            industry_target=industry,
            status='ACTIVE'
        )

        leads = Lead.objects.filter(workspace=ws, industry=industry)[:20]
        if not leads.exists():
            leads = Lead.objects.filter(workspace=ws)[:15]

        for lead in leads:
            pitch = lead.ai_pitches.first()
            if not pitch:
                pitch = generate_ai_outreach_pitch(lead, sender_name=request.user.full_name or request.user.username, user=request.user)
            CampaignLead.objects.create(campaign=camp, lead=lead, pitch=pitch, status='PREPARED')

        messages.success(request, f"Campaign '{name}' launched with {len(leads)} prepared leads!")
        return redirect('outreach:detail', pk=camp.id)

    return render(request, 'outreach/create_campaign.html', {
        'industries': Lead.INDUSTRY_CHOICES,
    })


@login_required
def mark_campaign_lead_sent_view(request, campaign_id, lead_id):
    camp_lead = get_object_or_404(CampaignLead, campaign_id=campaign_id, lead_id=lead_id, campaign__workspace__owner=request.user)
    camp_lead.status = 'SENT'
    camp_lead.sent_at = timezone.now()
    camp_lead.save()

    lead = camp_lead.lead
    if lead.status == 'NEW':
        lead.status = 'CONTACTED'
        lead.save(update_fields=['status'])

    # Also log as LeadMessage
    if camp_lead.pitch:
        LeadMessage.objects.create(
            lead=lead,
            channel='EMAIL',
            direction='OUTBOUND',
            sender=request.user.email,
            recipient=lead.email or lead.business_name,
            subject=camp_lead.pitch.subject,
            body=camp_lead.pitch.email_body
        )

    messages.success(request, f"Outreach marked as sent for {lead.business_name}!")
    return redirect('outreach:detail', pk=campaign_id)


# ==========================================
# 🚀 DIRECT SENDING & INBOUND RESPONSE VIEWS
# ==========================================

@login_required
def send_direct_email_view(request, lead_id):
    """
    Sends the pitch from the USER'S OWN mailbox (Settings > Email) and logs it.
    The email is only logged as sent if it really was sent.
    """
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)

    if request.method == 'POST':
        subject = request.POST.get('subject', f"Digital Growth Opportunity for {lead.business_name}")
        body = request.POST.get('body', '')
        recipient_email = request.POST.get('recipient_email', lead.email).strip()

        if not recipient_email:
            messages.error(request, f"Cannot send email: {lead.business_name} has no email address.")
            return redirect('leads:detail', pk=lead.id)

        link = ''
        if request.POST.get('include_portfolio'):
            link = portfolio_link(request, request.user, lead.workspace)
            if not link:
                messages.info(request, "Portfolio link was skipped: add at least one published project in Portfolio first.")
        full_body = compose_message(request.user, body, link)

        try:
            send_user_email(request.user, recipient_email, subject, full_body)
        except MailerError as exc:
            messages.error(request, f"Email NOT sent. {exc}")
            return redirect('leads:detail', pk=lead.id)

        if link and is_local_link(request, request.user):
            messages.warning(request, "Your portfolio link points to localhost, so the client cannot open it. Set your Public site URL in Settings > Agency & Portfolio.")

        LeadMessage.objects.create(
            lead=lead,
            channel='EMAIL',
            direction='OUTBOUND',
            sender=request.user.email,
            recipient=recipient_email,
            subject=subject,
            body=full_body
        )

        if lead.status == 'NEW':
            lead.status = 'CONTACTED'
            lead.save(update_fields=['status'])

        CRMActivity.objects.create(
            lead=lead,
            user=request.user,
            activity_type='EMAIL_SENT',
            description=f"Sent email: '{subject}' to {recipient_email}"
        )

        messages.success(request, f"Email sent to {lead.business_name} ({recipient_email}) from your own mailbox.")

    return redirect('leads:detail', pk=lead.id)


@login_required
def send_direct_whatsapp_view(request, lead_id):
    """
    Opens WhatsApp (your own account) with the message pre-filled for the lead, and logs it.
    """
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)
    body = request.POST.get('body') or request.GET.get('body', '')
    custom_phone = request.POST.get('phone', '').strip() or lead.phone
    user_settings = get_user_settings(request.user)

    clean_phone = clean_whatsapp_number(custom_phone, user_settings.default_country_code)
    if not clean_phone:
        messages.error(request, f"{lead.business_name} does not have a valid phone/WhatsApp number.")
        return redirect('leads:detail', pk=lead.id)

    if request.POST.get('include_portfolio'):
        link = portfolio_link(request, request.user, lead.workspace)
        if link:
            body = f"{body.rstrip()}\n\nMy recent live projects: {link}"
            if is_local_link(request, request.user):
                messages.warning(request, "Your portfolio link points to localhost, so the client cannot open it. Set your Public site URL in Settings > Agency & Portfolio.")

    LeadMessage.objects.create(
        lead=lead,
        channel='WHATSAPP',
        direction='OUTBOUND',
        sender=request.user.full_name or request.user.username,
        recipient=clean_phone,
        body=body
    )

    if lead.status == 'NEW':
        lead.status = 'CONTACTED'
        lead.save(update_fields=['status'])

    CRMActivity.objects.create(
        lead=lead,
        user=request.user,
        activity_type='CALL',
        description=f"Opened WhatsApp chat with {clean_phone} (message pre-filled)"
    )

    encoded_text = urllib.parse.quote(body)
    whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_text}"
    return redirect(whatsapp_url)


@login_required
def log_inbound_reply_view(request, lead_id):
    """
    Allows Shahwaiz to record an incoming client reply (from WhatsApp, Email, or Call)
    and automatically transitions the lead to REPLIED or INTERESTED stage.
    """
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)

    if request.method == 'POST':
        channel = request.POST.get('channel', 'WHATSAPP')
        reply_text = request.POST.get('reply_text', '').strip()
        new_status = request.POST.get('new_status', 'REPLIED')

        if reply_text:
            LeadMessage.objects.create(
                lead=lead,
                channel=channel,
                direction='INBOUND',
                sender=lead.business_name,
                recipient=request.user.full_name or request.user.username,
                body=reply_text
            )

            # Update stage
            lead.status = new_status
            lead.save(update_fields=['status'])

            CRMActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='NOTE',
                description=f"Received client reply via {channel}: '{reply_text[:60]}...'"
            )

            messages.success(request, f"Client response recorded for {lead.business_name}! Stage updated to {lead.get_status_display()}.")

    return redirect('leads:detail', pk=lead.id)


@login_required
def communications_inbox_view(request):
    """
    Unified Inbox showing all direct WhatsApp and Email conversations across all leads.
    """
    workspace = request.user.owned_workspaces.first()
    messages_list = LeadMessage.objects.filter(lead__workspace=workspace).select_related('lead').order_by('-created_at')

    # Quick metrics
    total_messages = messages_list.count()
    inbound_count = messages_list.filter(direction='INBOUND').count()
    outbound_count = messages_list.filter(direction='OUTBOUND').count()

    context = {
        'messages': messages_list,
        'total_messages': total_messages,
        'inbound_count': inbound_count,
        'outbound_count': outbound_count,
    }
    return render(request, 'outreach/inbox.html', context)


# ==========================================
# 📧 EMAIL TEMPLATES MANAGEMENT
# ==========================================

from .models import EmailTemplate
from apps.proposals.models import Proposal

def render_template_for_lead(template, lead, sender_user, proposal=None):
    """Replaces placeholders in template subject and body with lead details."""
    p_link = ''
    if proposal:
        p_link = f"/p/{proposal.access_token}/"
    else:
        existing_p = lead.proposals.first()
        if existing_p:
            p_link = f"/p/{existing_p.access_token}/"

    replacements = {
        '{{business_name}}': lead.business_name,
        '{{website}}': lead.website or 'your website',
        '{{city}}': lead.city or 'your city',
        '{{industry}}': lead.industry or 'business',
        '{{sender_name}}': sender_user.full_name or sender_user.username,
        '{{proposal_link}}': p_link,
    }

    subject = template.subject
    body = template.body

    for key, val in replacements.items():
        subject = subject.replace(key, str(val))
        body = body.replace(key, str(val))

    return subject, body


@login_required
def email_templates_list_view(request):
    templates = EmailTemplate.objects.filter(user=request.user).order_by('-is_default', 'category', 'name')
    return render(request, 'outreach/templates_list.html', {'templates': templates})


@login_required
def email_template_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'Cold Outreach')
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        is_default = request.POST.get('is_default') == 'on'

        if is_default:
            EmailTemplate.objects.filter(user=request.user).update(is_default=False)

        EmailTemplate.objects.create(
            user=request.user,
            name=name,
            category=category,
            subject=subject,
            body=body,
            is_default=is_default
        )
        messages.success(request, f"Email template '{name}' created successfully!")
        return redirect('outreach:templates_list')

    return render(request, 'outreach/template_form.html', {'title': 'Create New Email Template'})


@login_required
def email_template_edit_view(request, pk):
    template = get_object_or_404(EmailTemplate, id=pk, user=request.user)

    if request.method == 'POST':
        template.name = request.POST.get('name', '').strip()
        template.category = request.POST.get('category', 'Cold Outreach')
        template.subject = request.POST.get('subject', '').strip()
        template.body = request.POST.get('body', '').strip()
        is_default = request.POST.get('is_default') == 'on'

        if is_default:
            EmailTemplate.objects.filter(user=request.user).exclude(id=template.id).update(is_default=False)
        template.is_default = is_default

        template.save()
        messages.success(request, f"Email template '{template.name}' updated!")
        return redirect('outreach:templates_list')

    return render(request, 'outreach/template_form.html', {
        'template': template,
        'title': f"Edit Template: {template.name}"
    })


@login_required
def email_template_delete_view(request, pk):
    template = get_object_or_404(EmailTemplate, id=pk, user=request.user)
    name = template.name
    template.delete()
    messages.success(request, f"Template '{name}' was deleted.")
    return redirect('outreach:templates_list')


@login_required
def email_template_parse_api(request, template_id, lead_id):
    template = get_object_or_404(EmailTemplate, id=template_id, user=request.user)
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)
    subject, body = render_template_for_lead(template, lead, request.user)
    return JsonResponse({'success': True, 'subject': subject, 'body': body})

