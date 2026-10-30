from django.db import models
from apps.accounts.models import Workspace
from apps.leads.models import Lead
from apps.ai_engine.models import AIPitch

class Campaign(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active / In Progress'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
    )

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=200)
    industry_target = models.CharField(max_length=100, default='Restaurant')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def total_leads_count(self):
        return self.campaign_leads.count()

    @property
    def sent_count(self):
        return self.campaign_leads.filter(status='SENT').count()

    @property
    def replies_count(self):
        return self.campaign_leads.filter(status='REPLIED').count()

    @property
    def interested_count(self):
        return self.campaign_leads.filter(status='INTERESTED').count()


class CampaignLead(models.Model):
    STATUS_CHOICES = (
        ('PREPARED', 'Prepared'),
        ('SENT', 'Sent'),
        ('REPLIED', 'Replied'),
        ('INTERESTED', 'Interested'),
    )

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_leads')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    pitch = models.ForeignKey(AIPitch, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PREPARED')
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('campaign', 'lead')

    def __str__(self):
        return f"{self.campaign.name} - {self.lead.business_name} ({self.status})"


class LeadMessage(models.Model):
    CHANNEL_CHOICES = (
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Email'),
    )
    DIRECTION_CHOICES = (
        ('OUTBOUND', 'Outbound (Sent)'),
        ('INBOUND', 'Inbound (Client Reply)'),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='messages')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='WHATSAPP')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='OUTBOUND')
    sender = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.get_channel_display()}] {self.direction} - {self.lead.business_name}"


class EmailTemplate(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='email_templates')
    name = models.CharField('Template Name', max_length=150)
    category = models.CharField(max_length=50, default='Cold Outreach', choices=(
        ('Cold Outreach', 'Cold Outreach'),
        ('Follow-up', 'Follow-up'),
        ('Proposal Dispatch', 'Proposal Dispatch'),
        ('Closing', 'Closing / Won'),
        ('Custom', 'Custom'),
    ))
    subject = models.CharField('Subject Line', max_length=255)
    body = models.TextField('Template Body', help_text='Variables: {{business_name}}, {{website}}, {{city}}, {{industry}}, {{sender_name}}, {{proposal_link}}')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"

