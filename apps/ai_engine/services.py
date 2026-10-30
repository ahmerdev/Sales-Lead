from django.conf import settings
from .models import AIPitch

def generate_ai_outreach_pitch(lead, sender_name="", user=None):
    """
    Generates tailored, high-converting outreach email based on discovered gaps.
    Integrates with Google Gemini API when GEMINI_API_KEY is available,
    with a graceful high-quality heuristic fallback.
    """
    opportunities = list(lead.opportunities.all())
    opp_titles = [opp.title for opp in opportunities]
    opp_summary = ", ".join(opp_titles) if opp_titles else "General Digital Optimization"

    subject = f"Quick idea for {lead.business_name}"
    email_body = ""

    # Use the signed-in user's own Gemini key (Settings > API Keys), else the project-wide .env key.
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    agency_name = ''
    if user is not None:
        from apps.accounts.services import get_user_settings
        user_settings = get_user_settings(user)
        api_key = user_settings.gemini_api_key or api_key
        agency_name = user_settings.agency_name
        sender_name = sender_name or user.full_name or user.username
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""
            You are a world-class B2B digital agency consultant writing a short, consultative, high-converting cold email pitch.
            
            Business Name: {lead.business_name}
            Industry: {lead.industry}
            Location: {lead.city}, {lead.country}
            Detected Website & Conversion Gaps:
            {chr(10).join(['- ' + t for t in opp_titles]) if opp_titles else '- Missing modern mobile conversion hooks and direct ordering/booking'}
            
            Sender Name: {sender_name}
            
            Requirements:
            1. First line should be: Subject: [Catchy, low-pressure subject line]
            2. Friendly, non-salesy, consultative tone (under 120 words).
            3. Highlight 1-2 major detected gaps without shaming them.
            4. Offer a quick free value preview / loom video or demo.
            5. Clear, soft call to action.
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            text = response.text.strip()
            if "Subject:" in text:
                parts = text.split("Subject:", 1)[1].split("\n", 1)
                subject = parts[0].strip()
                email_body = parts[1].strip() if len(parts) > 1 else text
            else:
                email_body = text
        except Exception:
            # Fallback to smart heuristic generator below
            email_body = ""

    if not email_body:
        # High-converting smart cold pitch template adhering strictly to blueprint
        primary_gap = opp_titles[0] if opp_titles else "a modern direct online ordering and booking option"
        secondary_gap = f" and {opp_titles[1].lower()}" if len(opp_titles) > 1 else ""

        email_body = f"""Hi {lead.business_name} Team,

I was reviewing your website ({lead.website or lead.business_name}) and noticed that customers don't currently have {primary_gap.lower()}{secondary_gap}.

We help {lead.industry.lower()} businesses add simple ordering, booking, and WhatsApp lead capture systems without replacing their existing website.

If this is something you're considering to increase direct customer conversions, I'd be happy to share a quick 2-minute example of how this looks in action.

Regards,
{sender_name}{chr(10) + agency_name if agency_name else ''}"""

    pitch = AIPitch.objects.create(
        lead=lead,
        subject=subject,
        email_body=email_body,
        detected_opportunities_summary=opp_summary,
        status='DRAFT'
    )
    return pitch
