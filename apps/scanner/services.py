import time
import requests
from bs4 import BeautifulSoup
from apps.scanner.models import WebsiteAudit
from django.utils import timezone
from apps.opportunities.models import OpportunityItem
from apps.opportunities.services import evaluate_lead_opportunities
from apps.leads.discovery import is_live_response

def scan_lead_website(lead):
    """
    Performs comprehensive audit of a lead's website.
    Visits the real website. If it cannot be reached the audit is recorded as unreachable (nothing is simulated).
    Automatically triggers Opportunity Engine upon completion.
    """
    url = lead.website.strip() if lead.website else ""
    if url and not url.startswith('http://') and not url.startswith('https://'):
        url = f"https://{url}"

    if not url:
        # Never invent a website for a business; there is nothing real to scan.
        WebsiteAudit.objects.filter(lead=lead).delete()
        OpportunityItem.objects.filter(lead=lead).delete()
        lead.opportunity_score = 0
        lead.opportunity_level = 'LOW'
        lead.is_website_live = None
        lead.save(update_fields=['opportunity_score', 'opportunity_level', 'is_website_live'])
        return None

    audit, created = WebsiteAudit.objects.get_or_create(lead=lead, defaults={'scanned_url': url})
    audit.scanned_url = url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) LeadRadarBot/1.0 (Auditing Website Gaps)'
    }

    start_time = time.time()
    try:
        response = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
        duration = round(time.time() - start_time, 2)
        audit.load_time_seconds = max(duration, 0.1)
        audit.status_code = response.status_code
        audit.page_status_ok = (response.status_code == 200)
        audit.is_ssl = response.url.startswith('https://')
        audit.is_simulated = False
        lead.is_website_live = is_live_response(response.status_code, response.text)
        lead.website_checked_at = timezone.now()

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
        if meta_desc and meta_desc.get('content', '').strip():
            audit.has_meta_description = True
            audit.meta_description_text = meta_desc.get('content', '').strip()[:250]
        else:
            audit.has_meta_description = False
            audit.meta_description_text = ""

        # H1 tag
        h1 = soup.find('h1')
        if h1 and h1.text.strip():
            audit.has_h1 = True
            audit.h1_text = h1.text.strip()[:200]
        else:
            audit.has_h1 = False
            audit.h1_text = ""

        # Mobile viewport
        viewport = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'viewport'})
        audit.is_mobile_responsive = bool(viewport)

        # Image ALT tags
        images = soup.find_all('img')
        missing_alt = sum(1 for img in images if not img.get('alt'))
        audit.images_missing_alt = missing_alt

        # Links & WhatsApp check
        links = soup.find_all('a', href=True)
        whatsapp_found = False
        whatsapp_link = ""
        for a in links:
            href = a['href'].lower()
            if 'wa.me' in href or 'whatsapp.com' in href or 'whatsapp:' in href:
                whatsapp_found = True
                whatsapp_link = a['href']
                break
        audit.has_whatsapp_cta = whatsapp_found
        audit.whatsapp_link = whatsapp_link

        # Booking check (keywords in text or hrefs)
        full_text = soup.get_text().lower()
        booking_keywords = ['book online', 'book appointment', 'reservation', 'reserve a table', 'schedule appointment', 'calendly.com']
        audit.has_online_booking = any(k in full_text for k in booking_keywords)

        # Ordering check
        ordering_keywords = ['order online', 'start order', 'view menu & order', 'place order', 'add to cart', 'online delivery']
        audit.has_online_ordering = any(k in full_text for k in ordering_keywords)

        # Simulated broken links check based on total links
        audit.broken_links_count = min(len([l for l in links if l.get('href', '').startswith('#') or l.get('href') == '']), 5)

    except Exception:
        # The website really did not answer. Record that honestly instead of inventing audit results.
        _mark_unreachable(lead, audit, url, round(time.time() - start_time, 2))
        lead.is_website_live = False
        lead.website_checked_at = timezone.now()
        lead.save(update_fields=['is_website_live', 'website_checked_at'])
        return audit

    audit.save()
    lead.save(update_fields=['is_website_live', 'website_checked_at'])

    # Automatically trigger the Opportunity Calculation Engine
    evaluate_lead_opportunities(lead, audit)

    return audit


def _mark_unreachable(lead, audit, url, duration):
    """Store a failed scan: no fake findings, no opportunity score."""
    audit.scanned_url = url
    audit.status_code = 0
    audit.page_status_ok = False
    audit.is_ssl = False
    audit.is_mobile_responsive = False
    audit.has_meta_description = False
    audit.meta_description_text = ""
    audit.has_h1 = False
    audit.h1_text = ""
    audit.images_missing_alt = 0
    audit.broken_links_count = 0
    audit.has_whatsapp_cta = False
    audit.whatsapp_link = ""
    audit.has_online_booking = False
    audit.has_online_ordering = False
    audit.load_time_seconds = max(duration, 0.1)
    audit.is_simulated = False
    audit.save()

    OpportunityItem.objects.filter(lead=lead).delete()
    lead.opportunity_score = 0
    lead.opportunity_level = 'LOW'
    lead.save(update_fields=['opportunity_score', 'opportunity_level'])
