from django.db import models
from apps.accounts.models import Workspace


class PortfolioItem(models.Model):
    """One live project the agency shows to prospects to build trust."""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=200, help_text='e.g. "Online ordering website for Saffron Bistro"')
    client_name = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=100, blank=True, help_text='e.g. Restaurant, Dental, Real Estate')
    live_url = models.URLField(blank=True, help_text='Link to the live website so the client can open it')
    image = models.FileField(upload_to='portfolio/', blank=True, help_text='Screenshot of the project (PNG/JPG)')
    image_url = models.URLField(blank=True, help_text='Or paste an image link instead of uploading')
    description = models.TextField(blank=True)
    badge_text = models.CharField(max_length=100, blank=True, default='', help_text='e.g. "1-CLICK ORDERING" or "$12M+ PIPELINE"')
    technologies = models.CharField(max_length=255, blank=True, default='Next.js 14, WhatsApp API, Stripe Connect', help_text='Comma-separated tech badges, e.g. "Next.js 14, WhatsApp API, Stripe Connect"')
    results = models.CharField(max_length=255, blank=True, help_text='A real result, e.g. "+40% direct orders in 3 months"')
    testimonial = models.TextField(blank=True, help_text='Only add real client feedback')
    testimonial_author = models.CharField(max_length=150, blank=True)
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0, help_text='Lower numbers appear first')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title

    @property
    def cover(self):
        if self.image:
            return self.image.url
        return self.image_url

    @property
    def tech_list(self):
        if not self.technologies:
            return []
        parts = [t.strip() for t in self.technologies.replace('•', ',').replace('|', ',').split(',')]
        return [p for p in parts if p]

    @property
    def clean_domain(self):
        if self.live_url:
            u = self.live_url.replace('https://', '').replace('http://', '').strip('/')
            return u.split('/')[0]
        from django.utils.text import slugify
        return f"{slugify(self.title or 'project')}.com"

    @property
    def quote(self):
        return self.testimonial

    @property
    def author(self):
        return self.testimonial_author or self.client_name

    @property
    def role_display(self):
        return self.client_name or self.industry


class PortfolioFAQ(models.Model):
    """Client FAQs shown on the public agency portfolio page, managed by each user."""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=300)
    answer = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return self.question


class PortfolioTestimonial(models.Model):
    """Client reviews & testimonials shown on the public portfolio page, managed by each user."""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='testimonials')
    client_name = models.CharField(max_length=150)
    client_role = models.CharField(max_length=150, blank=True, help_text='e.g. Managing Partner, Saffron Bistro')
    company_name = models.CharField(max_length=150, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    feedback = models.TextField()
    avatar_url = models.URLField(blank=True)
    project_title = models.CharField(max_length=150, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f"{self.client_name} ({self.company_name or self.client_role})"

    @property
    def quote(self):
        return self.feedback

    @property
    def author(self):
        return self.client_name

    @property
    def role_display(self):
        return self.client_role or self.company_name or 'Verified Client'


