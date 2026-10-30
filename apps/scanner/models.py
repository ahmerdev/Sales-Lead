from django.db import models
from apps.leads.models import Lead

class WebsiteAudit(models.Model):
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, related_name='audit')
    scanned_url = models.URLField(max_length=500)
    
    # Audit Flags
    status_code = models.IntegerField(default=200)
    is_ssl = models.BooleanField(default=False)
    is_mobile_responsive = models.BooleanField(default=False)
    page_status_ok = models.BooleanField(default=True)
    
    # SEO Signals
    has_meta_description = models.BooleanField(default=False)
    meta_description_text = models.TextField(blank=True)
    has_h1 = models.BooleanField(default=False)
    h1_text = models.CharField(max_length=300, blank=True)
    images_missing_alt = models.IntegerField(default=0)
    broken_links_count = models.IntegerField(default=0)
    
    # Conversion CTA Signals
    has_whatsapp_cta = models.BooleanField(default=False)
    whatsapp_link = models.CharField(max_length=300, blank=True)
    has_online_booking = models.BooleanField(default=False)
    has_online_ordering = models.BooleanField(default=False)
    
    # Performance & Diagnostics
    load_time_seconds = models.FloatField(default=0.8)
    is_simulated = models.BooleanField(default=False, help_text="True if domain was unreachable and fallback smart audit ran")
    scanned_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Audit for {self.lead.business_name} ({self.scanned_url})"
