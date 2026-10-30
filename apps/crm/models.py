from django.db import models
from django.utils import timezone
from apps.leads.models import Lead
from apps.accounts.models import User

class CRMActivity(models.Model):
    ACTIVITY_TYPE_CHOICES = (
        ('NOTE', 'Note Added'),
        ('STATUS_CHANGE', 'Stage Changed'),
        ('EMAIL_SENT', 'Email Sent'),
        ('CALL', 'Phone Call'),
        ('MEETING', 'Client Meeting'),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='crm_activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPE_CHOICES, default='NOTE')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.activity_type} on {self.lead.business_name}"


class FollowUp(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups')
    scheduled_date = models.DateField()
    notes = models.CharField(max_length=255, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_completed', 'scheduled_date']

    def __str__(self):
        return f"Follow up for {self.lead.business_name} on {self.scheduled_date}"

    def mark_as_completed(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
