from .models import OpportunityItem

def evaluate_lead_opportunities(lead, audit):
    """
    Transparent Rule-based Opportunity Engine:
    Converts raw website scanner telemetry into concrete, high-ticket agency services
    and calculates a deterministic Opportunity Score (0 - 100).
    """
    # Clear existing items
    OpportunityItem.objects.filter(lead=lead).delete()

    opportunities_to_create = []
    total_score = 0

    # Rule 1: No WhatsApp CTA (+15 pts)
    if not audit.has_whatsapp_cta:
        score = 15
        total_score += score
        opportunities_to_create.append(OpportunityItem(
            lead=lead,
            title="Missing WhatsApp Fast Contact CTA",
            description="The website lacks a floating WhatsApp or direct chat button, losing potential mobile leads who prefer instant messaging.",
            score_impact=score,
            recommended_service="WhatsApp Quick Connect & Automated Chat Setup",
            category='CONVERSION'
        ))

    # Rule 2: No Online Ordering (+20 pts)
    # High impact especially for Restaurant, E-Commerce, Retail
    if not audit.has_online_ordering:
        score = 20
        total_score += score
        opportunities_to_create.append(OpportunityItem(
            lead=lead,
            title="No Direct Online Ordering System",
            description="Customers cannot order food, services, or products directly on the website, leaking revenue to high-commission third-party portals.",
            score_impact=score,
            recommended_service="Direct Online Ordering & Menu Ordering Portal",
            category='SALES'
        ))

    # Rule 3: No Online Booking (+15 pts)
    # High impact for Dental, Healthcare, Fitness, Real Estate, Legal
    if not audit.has_online_booking:
        score = 15
        total_score += score
        opportunities_to_create.append(OpportunityItem(
            lead=lead,
            title="Lacks Online Booking / Appointment Scheduling",
            description="Site relies on static phone numbers instead of a seamless calendar booking system, creating friction for busy clients.",
            score_impact=score,
            recommended_service="Automated 24/7 Booking & Calendar Integration",
            category='BOOKING'
        ))

    # Rule 4: SEO Basics / Missing Meta Description (+15 pts)
    if not audit.has_meta_description or not audit.has_h1:
        score = 15
        total_score += score
        missing = []
        if not audit.has_meta_description:
            missing.append("meta description")
        if not audit.has_h1:
            missing.append("H1 heading")
        opportunities_to_create.append(OpportunityItem(
            lead=lead,
            title=f"Missing Basic SEO ({', '.join(missing)})",
            description="Search engines like Google struggle to index and rank the site properly because foundational on-page tags are absent.",
            score_impact=score,
            recommended_service="On-Page SEO Optimization & Local Google Ranking",
            category='SEO'
        ))

    # Rule 5: SSL Insecurity (+15 pts)
    if not audit.is_ssl:
        score = 15
        total_score += score
        opportunities_to_create.append(OpportunityItem(
            lead=lead,
            title="Insecure Website (Missing SSL / HTTPS)",
            description="Browsers mark the site as 'Not Secure', scaring away high-value customers and hurting organic search rankings.",
            score_impact=score,
            recommended_service="SSL Certificate Installation & HTTPS Security Migration",
            category='TECHNICAL'
        ))

    # Rule 6: Technical Issues / Broken Links (+10 pts)
    if audit.broken_links_count > 0 or audit.images_missing_alt > 3:
        score = 10
        total_score += score
        issues = []
        if audit.broken_links_count > 0:
            issues.append(f"{audit.broken_links_count} broken links")
        if audit.images_missing_alt > 3:
            issues.append(f"{audit.images_missing_alt} unoptimized images")
        opportunities_to_create.append(OpportunityItem(
            lead=lead,
            title=f"Technical Deficiencies ({', '.join(issues)})",
            description="Broken links and missing image tags degrade user experience and trigger Google core web vital penalties.",
            score_impact=score,
            recommended_service="Website Maintenance & Technical Audit Cleanup",
            category='TECHNICAL'
        ))

    # Rule 7: Mobile Responsiveness (+10 pts)
    if not audit.is_mobile_responsive:
        score = 10
        total_score += score
        opportunities_to_create.append(OpportunityItem(
            lead=lead,
            title="Poor Mobile Viewport Optimization",
            description="The site is difficult to navigate on mobile devices, where over 70% of local customers browse.",
            score_impact=score,
            recommended_service="Mobile-First Responsive Layout Redesign",
            category='CONVERSION'
        ))

    # Bulk create opportunity items
    OpportunityItem.objects.bulk_create(opportunities_to_create)

    # Cap score at 100
    final_score = min(total_score, 100)
    lead.opportunity_score = final_score
    if final_score >= 70:
        lead.opportunity_level = 'HIGH'
    elif final_score >= 40:
        lead.opportunity_level = 'MEDIUM'
    else:
        lead.opportunity_level = 'LOW'

    lead.save(update_fields=['opportunity_score', 'opportunity_level'])
    return final_score, opportunities_to_create
