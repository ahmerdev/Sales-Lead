from django.db import models
from apps.accounts.models import Workspace

class Lead(models.Model):
    INDUSTRY_CHOICES = (
        ('Restaurant', 'Restaurant & Cafe'),
        ('Dental', 'Dental & Clinic'),
        ('Fitness', 'Fitness & Gym'),
        ('Real Estate', 'Real Estate & Property'),
        ('E-Commerce', 'E-Commerce & Retail'),
        ('Healthcare', 'Healthcare & Medical'),
        ('Legal', 'Legal & Law Firm'),
        ('Hospitality', 'Hospitality & Hotel'),
        ('Automotive', 'Automotive & Garage'),
        ('Home Services', 'Home Services & Repairs'),
        ('Manufacturing', 'Manufacturing & Industry'),
        ('Other', 'Other Industry'),
    )

    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('REPLIED', 'Replied'),
        ('INTERESTED', 'Interested'),
        ('PROPOSAL', 'Proposal Sent'),
        ('WON', 'Won / Closed'),
        ('LOST', 'Lost'),
    )

    OPPORTUNITY_LEVEL_CHOICES = (
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    )

    SOURCE_CHOICES = (
        ('MANUAL', 'Manual Entry'),
        ('CSV_IMPORT', 'CSV Import'),
        ('DISCOVERY', 'Lead Discovery Engine'),
        ('OSM', 'OpenStreetMap (Real Business Data)'),
    )

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='leads')
    business_name = models.CharField(max_length=255)
    website = models.URLField(max_length=500, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='United Arab Emirates')
    industry = models.CharField(max_length=100, choices=INDUSTRY_CHOICES, default='Restaurant')
    
    # Opportunity Scoring
    opportunity_score = models.IntegerField(default=0)  # 0 to 100
    opportunity_level = models.CharField(max_length=20, choices=OPPORTUNITY_LEVEL_CHOICES, default='LOW')
    
    # Sales Lifecycle
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='NEW')
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='MANUAL')
    notes = models.TextField(blank=True)

    # Real-data tracking
    external_id = models.CharField(max_length=100, blank=True, db_index=True, help_text='ID from the source (e.g. OpenStreetMap node/123) used to avoid duplicates')
    is_website_live = models.BooleanField(null=True, blank=True, help_text='None = never checked, True = reachable, False = dead/unreachable')
    website_checked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-opportunity_score', '-created_at']

    def __str__(self):
        return f"{self.business_name} ({self.industry})"

    def clean_website(self):
        if self.website and not (self.website.startswith('http://') or self.website.startswith('https://')):
            return f"https://{self.website}"
        return self.website

    def save(self, *args, **kwargs):
        if self.website:
            self.website = self.clean_website()
        
        # Auto-update opportunity level based on score
        if self.opportunity_score >= 70:
            self.opportunity_level = 'HIGH'
        elif self.opportunity_score >= 40:
            self.opportunity_level = 'MEDIUM'
        else:
            self.opportunity_level = 'LOW'
            
        super().save(*args, **kwargs)


class LeadContact(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=150)
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.lead.business_name}"
