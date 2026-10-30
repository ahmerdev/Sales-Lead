from django.db import models
from apps.leads.models import Lead

class AIPitch(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('APPROVED', 'Approved'),
        ('SENT', 'Sent'),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='ai_pitches')
    subject = models.CharField(max_length=255)
    email_body = models.TextField()
    detected_opportunities_summary = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"AI Pitch for {self.lead.business_name} - {self.subject}"
