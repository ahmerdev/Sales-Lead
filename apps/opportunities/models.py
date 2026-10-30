from django.db import models
from apps.leads.models import Lead

class OpportunityItem(models.Model):
    CATEGORY_CHOICES = (
        ('CONVERSION', 'Conversion & CTAs'),
        ('SALES', 'Sales & Ordering'),
        ('BOOKING', 'Booking & Appointments'),
        ('SEO', 'SEO & Visibility'),
        ('TECHNICAL', 'Technical & Performance'),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='opportunities')
    title = models.CharField(max_length=255)
    description = models.TextField()
    score_impact = models.IntegerField(default=15)
    recommended_service = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='CONVERSION')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.business_name} - {self.title} (+{self.score_impact} pts)"
