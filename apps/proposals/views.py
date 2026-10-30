import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from apps.leads.models import Lead
from apps.crm.models import CRMActivity
from apps.outreach.models import LeadMessage
from apps.accounts.services import (
    get_user_settings, send_user_email, compose_message, MailerError,
    portfolio_link, public_url as build_public_url, is_local_link,
    clean_whatsapp_number, whatsapp_link,
)
from .models import Proposal

@login_required
def create_proposal_for_lead(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id, workspace__owner=request.user)

    if request.method == 'POST':
        title = request.POST.get('title') or f"Website & Digital Growth Proposal for {lead.business_name}"
        scope = request.POST.get('scope_summary')
        timeline = request.POST.get('timeline') or "14–21 business days"
        amount = request.POST.get('investment_amount') or 750.00
        currency = request.POST.get('currency') or "USD"

        proposal = Proposal.objects.create(
            lead=lead,
            title=title,
            client_name=lead.business_name,
            scope_summary=scope,
            timeline=timeline,
            investment_amount=amount,
            currency=currency,
            status='DRAFT'
        )

        lead.status = 'PROPOSAL'
        lead.save(update_fields=['status'])

        messages.success(request, f"Proposal created successfully for {lead.business_name}!")
        return redirect('proposals:detail', pk=proposal.id)

    opps = lead.opportunities.all()
    if opps.exists():
        default_scope = "\n".join([f"• {opp.recommended_service}: {opp.description}" for opp in opps])
    else:
        default_scope = "• Direct Online Ordering System Integration\n• WhatsApp Instant Lead Capture CTA\n• 24/7 Automated Booking & Calendar\n• Complete On-Page SEO Optimization"

    context = {
        'lead': lead,
        'default_scope': default_scope,
    }
    return render(request, 'proposals/create.html', context)


@login_required
def proposal_detail_view(request, pk):
    proposal = get_object_or_404(Proposal, id=pk, lead__workspace__owner=request.user)
    public_url = build_public_url(request, request.user, f"/p/{proposal.access_token}/")
    return render(request, 'proposals/detail.html', {
        'proposal': proposal,
        'public_url': public_url,
        'local_link_warning': is_local_link(request, request.user),
    })


@login_required
def proposals_list_view(request):
    proposals = Proposal.objects.filter(lead__workspace__owner=request.user).order_by('-created_at')
    return render(request, 'proposals/list.html', {'proposals': proposals})


@login_required
def cancel_proposal_view(request, pk):
    proposal = get_object_or_404(Proposal, id=pk, lead__workspace__owner=request.user)
    if request.method == 'POST':
        action = request.POST.get('action', 'cancel')
        if action == 'reopen':
            proposal.status = 'DRAFT'
            proposal.save(update_fields=['status'])
            CRMActivity.objects.create(
                lead=proposal.lead,
                user=request.user,
                activity_type='NOTE',
                description=f"Proposal #{proposal.id} was reopened as Draft by user."
            )
            messages.success(request, f"Proposal for {proposal.client_name} reopened as Draft.")
        else:
            proposal.status = 'CANCELLED'
            proposal.save(update_fields=['status'])
            CRMActivity.objects.create(
                lead=proposal.lead,
                user=request.user,
                activity_type='NOTE',
                description=f"Proposal #{proposal.id} ({proposal.title}) was marked as CANCELLED."
            )
            messages.warning(request, f"Proposal for {proposal.client_name} has been cancelled.")
        return redirect('proposals:detail', pk=proposal.id)
    return redirect('proposals:detail', pk=proposal.id)


@login_required
def delete_proposal_view(request, pk):
    proposal = get_object_or_404(Proposal, id=pk, lead__workspace__owner=request.user)
    if request.method == 'POST':
        client_name = proposal.client_name
        lead = proposal.lead
        proposal.delete()
        CRMActivity.objects.create(
            lead=lead,
            user=request.user,
            activity_type='NOTE',
            description=f"Proposal for {client_name} was permanently deleted."
        )
        messages.success(request, f"Proposal for {client_name} has been permanently deleted.")
        return redirect('proposals:list')
    return redirect('proposals:detail', pk=proposal.id)


@login_required
def send_proposal_email_view(request, pk):
    """
    Sends the proposal link from the user's OWN mailbox (Settings > Email).
    """
    proposal = get_object_or_404(Proposal, id=pk, lead__workspace__owner=request.user)
    lead = proposal.lead
    recipient_email = request.POST.get('email', lead.email).strip()

    if not recipient_email:
        messages.error(request, f"Please enter an email address for {lead.business_name}.")
        return redirect('proposals:detail', pk=proposal.id)

    public_url = build_public_url(request, request.user, f"/p/{proposal.access_token}/")
    sender_name = request.user.full_name or request.user.username
    subject = f"Digital Growth Proposal for {proposal.client_name}"
    body = f"""Hi {proposal.client_name} Team,

Thank you for your interest. As discussed, I have prepared a tailored digital growth and website improvement proposal for you:

View Your Interactive Proposal Online:
{public_url}

Scope Summary:
{proposal.scope_summary}

Timeline: {proposal.timeline}
Total Investment: {proposal.currency} {proposal.investment_amount}

You can review the scope and accept the proposal directly online from the link above.

Regards,
{sender_name}"""

    link = portfolio_link(request, request.user, lead.workspace)
    full_body = compose_message(request.user, body, link)

    try:
        send_user_email(request.user, recipient_email, subject, full_body)
    except MailerError as exc:
        messages.error(request, f"Email NOT sent. {exc}")
        return redirect('proposals:detail', pk=proposal.id)

    if is_local_link(request, request.user):
        messages.warning(request, "The proposal link points to localhost, so the client cannot open it. Set your Public site URL in Settings > Agency & Portfolio.")

    proposal.status = 'SENT'
    proposal.save(update_fields=['status'])

    LeadMessage.objects.create(
        lead=lead,
        channel='EMAIL',
        direction='OUTBOUND',
        sender=request.user.email,
        recipient=recipient_email,
        subject=subject,
        body=full_body
    )

    CRMActivity.objects.create(
        lead=lead,
        user=request.user,
        activity_type='EMAIL_SENT',
        description=f"Sent official proposal '{proposal.title}' to {recipient_email}"
    )

    messages.success(request, f"Proposal emailed to {recipient_email} from your own mailbox.")
    return redirect('proposals:detail', pk=proposal.id)


@login_required
def send_proposal_whatsapp_view(request, pk):
    """
    Opens WhatsApp (your own account) with the proposal link pre-filled.
    """
    proposal = get_object_or_404(Proposal, id=pk, lead__workspace__owner=request.user)
    lead = proposal.lead
    user_settings = get_user_settings(request.user)
    clean_phone = clean_whatsapp_number(lead.phone, user_settings.default_country_code)

    if not clean_phone:
        messages.error(request, f"No valid WhatsApp number found for {lead.business_name}.")
        return redirect('proposals:detail', pk=proposal.id)

    public_url = build_public_url(request, request.user, f"/p/{proposal.access_token}/")
    sender_name = request.user.full_name or request.user.username
    body = f"""Hi {proposal.client_name} Team,

I've prepared your Website & Digital Improvement Proposal!

You can review the deliverables, timeline, and investment here:
{public_url}

• Timeline: {proposal.timeline}
• Investment: {proposal.currency} {proposal.investment_amount}

You can also accept the proposal directly from the link above."""

    link = portfolio_link(request, request.user, lead.workspace)
    if link:
        body += f"\n\nMy recent live projects: {link}"
    body += f"\n\nRegards,\n{sender_name}"

    if is_local_link(request, request.user):
        messages.warning(request, "The proposal link points to localhost, so the client cannot open it. Set your Public site URL in Settings > Agency & Portfolio.")

    proposal.status = 'SENT'
    proposal.save(update_fields=['status'])

    LeadMessage.objects.create(
        lead=lead,
        channel='WHATSAPP',
        direction='OUTBOUND',
        sender=sender_name,
        recipient=clean_phone,
        body=body
    )

    CRMActivity.objects.create(
        lead=lead,
        user=request.user,
        activity_type='CALL',
        description=f"Opened WhatsApp with the proposal link for {clean_phone}"
    )

    encoded_text = urllib.parse.quote(body)
    whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_text}"
    return redirect(whatsapp_url)


# ========================================================
# 🌐 PUBLIC CLIENT PORTAL: VIEW, ACCEPT & REPLY TO PROPOSAL
# ========================================================

def _public_context(request, proposal, **extra):
    """Agency identity + live portfolio shown to the client on the proposal page (builds trust)."""
    workspace = proposal.lead.workspace
    owner = workspace.owner
    agency = get_user_settings(owner)
    items = []
    if agency.portfolio_enabled:
        items = list(workspace.portfolio_items.filter(is_published=True)[:6])

    from .models import PortfolioProject
    portfolio_projects = list(PortfolioProject.objects.filter(user=owner, featured=True))
    if not portfolio_projects:
        portfolio_projects = list(PortfolioProject.objects.filter(user=owner))

    context = {
        'proposal': proposal,
        'owner': owner,
        'agency': agency,
        'portfolio_items': items,
        'featured_projects': portfolio_projects,
        'portfolio_url': portfolio_link(request, owner, workspace),
        'whatsapp_url': whatsapp_link(
            agency.whatsapp_number,
            f"Hi {agency.display_agency_name}, I'm {proposal.client_name}. I have a question about the proposal.",
        ),
        'contact_email': agency.reply_to or owner.email,
    }
    context.update(extra)
    return context


def public_proposal_view(request, token):
    """
    Public interactive landing page where the CLIENT views the proposal,
    accepts it, or sends a direct reply/question to Shahwaiz.
    """
    proposal = get_object_or_404(Proposal, access_token=token)

    # Record client view timestamp
    if not proposal.viewed_by_client_at:
        proposal.viewed_by_client_at = timezone.now()
        proposal.save(update_fields=['viewed_by_client_at'])

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            client_notes = request.POST.get('client_notes', '').strip()
            proposal.status = 'ACCEPTED'
            proposal.client_feedback = client_notes or "Accepted online by client"
            proposal.save(update_fields=['status', 'client_feedback'])

            # Advance lead stage to WON
            lead = proposal.lead
            lead.status = 'WON'
            lead.save(update_fields=['status'])

            # Log incoming message
            LeadMessage.objects.create(
                lead=lead,
                channel='EMAIL',
                direction='INBOUND',
                sender=proposal.client_name,
                recipient='Agency Team',
                subject="🎉 PROPOSAL ACCEPTED!",
                body=f"Client accepted the proposal!\n\nClient Note: {client_notes or 'Ready to proceed.'}"
            )

            CRMActivity.objects.create(
                lead=lead,
                activity_type='STATUS_CHANGE',
                description=f"🎉 Client accepted the proposal for {proposal.currency} {proposal.investment_amount}!"
            )

            return render(request, 'proposals/public_view.html', _public_context(request, proposal, accepted_just_now=True))

        elif action == 'reply':
            message_text = request.POST.get('message', '').strip()
            if message_text:
                lead = proposal.lead
                if lead.status in ['NEW', 'CONTACTED']:
                    lead.status = 'INTERESTED'
                    lead.save(update_fields=['status'])

                LeadMessage.objects.create(
                    lead=lead,
                    channel='EMAIL',
                    direction='INBOUND',
                    sender=proposal.client_name,
                    recipient='Agency Team',
                    subject=f"Question regarding {proposal.title}",
                    body=message_text
                )

                CRMActivity.objects.create(
                    lead=lead,
                    activity_type='NOTE',
                    description=f"Client replied on proposal: '{message_text}'"
                )

                return render(request, 'proposals/public_view.html', _public_context(request, proposal, reply_sent_just_now=True))

    return render(request, 'proposals/public_view.html', _public_context(request, proposal))
