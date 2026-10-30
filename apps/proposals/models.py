import uuid
from django.db import models
from apps.leads.models import Lead

class Proposal(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Client'),
        ('ACCEPTED', 'Accepted / Won'),
        ('DECLINED', 'Declined'),
        ('CANCELLED', 'Cancelled'),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='proposals')
    access_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    title = models.CharField(max_length=255, default="Website & Digital Growth Proposal")
    client_name = models.CharField(max_length=255)
    scope_summary = models.TextField(help_text="Detailed bullet points of deliverable services")
    timeline = models.CharField(max_length=100, default="14–21 business days")
    investment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=750.00)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, default="Payment schedule: 50% upfront deposit, 50% upon successful delivery and testing.")
    client_feedback = models.TextField(blank=True, help_text="Direct reply or acceptance notes from client")
    viewed_by_client_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.access_token:
            self.access_token = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Proposal for {self.client_name} ({self.currency} {self.investment_amount})"


class PortfolioProject(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='portfolio_projects')
    title = models.CharField('Project Title', max_length=200)
    category = models.CharField('Industry / Niche', max_length=100, default='Restaurant & Ordering')
    client_name = models.CharField('Client Name', max_length=150, blank=True)
    result_metric = models.CharField('Key Result Highlight', max_length=100, default='+340% Online Orders')
    description = models.TextField('Overview & What We Built')
    technologies = models.CharField('Tech / Services Delivered', max_length=255, default='WhatsApp POS • Online Ordering • Mobile UI')
    image_url = models.URLField('Project Image / Mockup URL', blank=True, default='')
    demo_url = models.URLField('Live Preview Link', blank=True, default='')
    featured = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.client_name or 'Case Study'})"

