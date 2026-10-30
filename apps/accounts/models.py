from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from .crypto import encrypt, decrypt

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    )
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    is_approved = models.BooleanField('Approved by Super Admin', default=False)
    avatar_url = models.URLField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.full_name or self.email or self.username


class Workspace(models.Model):
    PLAN_CHOICES = (
        ('free', 'Free ($0)'),
        ('starter', 'Starter ($9/mo)'),
        ('pro', 'Pro ($19/mo)'),
        ('agency', 'Agency ($49/mo)'),
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_workspaces')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='pro')
    max_leads = models.IntegerField(default=5000)
    max_scans = models.IntegerField(default=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or 'workspace'
            slug = base_slug
            counter = 1
            while Workspace.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspaces')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workspace', 'user')

    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"


class UserSettings(models.Model):
    """Per-user settings: own SMTP mailbox, WhatsApp, API keys and public agency branding."""
    SECURITY_CHOICES = (
        ('TLS', 'STARTTLS (usually port 587)'),
        ('SSL', 'SSL/TLS (usually port 465)'),
        ('NONE', 'None (not recommended)'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agency_settings')

    # --- Email (the user's own mailbox) ---
    smtp_host = models.CharField('SMTP host', max_length=255, blank=True, help_text='Gmail: smtp.gmail.com  |  Outlook: smtp.office365.com  |  Zoho: smtp.zoho.com')
    smtp_port = models.PositiveIntegerField('SMTP port', default=587)
    smtp_security = models.CharField('Security', max_length=10, choices=SECURITY_CHOICES, default='TLS')
    smtp_username = models.CharField('SMTP username', max_length=255, blank=True, help_text='Usually your full email address')
    smtp_password_enc = models.TextField(blank=True)
    from_name = models.CharField('Sender name', max_length=150, blank=True, help_text='Shown to clients, e.g. "Ali from Haq Chain"')
    from_email = models.EmailField('Sender email', blank=True, help_text='Leave empty to use your SMTP username. Must be allowed by your mail provider.')
    reply_to = models.EmailField('Reply-to email', blank=True, help_text='Where client replies should go. Leave empty to use your account email.')
    email_signature = models.TextField('Email signature', blank=True, help_text='Added at the end of every email. Leave empty if your messages already end with your name.')
    email_footer = models.TextField(
        'Opt-out line', blank=True,
        default="If you'd rather not hear from me, just reply \"stop\" and I won't contact you again.",
        help_text='Added under every cold email. Keeping an opt-out line is good practice and often legally required.')

    # --- WhatsApp ---
    whatsapp_number = models.CharField('Your WhatsApp number', max_length=30, blank=True, help_text='With country code, e.g. +92 300 1234567')
    default_country_code = models.CharField('Default country code', max_length=6, blank=True, help_text='Used for lead numbers that start with 0, e.g. 92 for Pakistan, 971 for UAE')
    whatsapp_default_message = models.TextField('Default WhatsApp message', blank=True)

    # --- API keys ---
    gemini_api_key_enc = models.TextField(blank=True)

    # --- Agency branding / public pages ---
    agency_name = models.CharField('Agency name', max_length=150, blank=True)
    agency_tagline = models.CharField('Tagline', max_length=200, blank=True)
    agency_about = models.TextField('About your agency', blank=True)
    agency_website = models.URLField('Agency website', blank=True)
    logo_url = models.URLField('Logo image URL', blank=True)
    logo_file = models.ImageField('Upload Agency Logo', upload_to='agency_logos/', blank=True, null=True)
    FONT_CHOICES = (
        ('Plus Jakarta Sans', 'Plus Jakarta Sans (Modern Clean)'),
        ('Inter', 'Inter (SaaS Standard)'),
        ('Space Grotesk', 'Space Grotesk (Tech & Agency)'),
        ('Outfit', 'Outfit (Futuristic & Sleek)'),
        ('Poppins', 'Poppins (Friendly Geometric)'),
        ('Montserrat', 'Montserrat (Bold Corporate)'),
        ('DM Sans', 'DM Sans (Minimalist Professional)'),
    )
    font_family = models.CharField('Typography / Font Family', max_length=60, choices=FONT_CHOICES, default='Plus Jakarta Sans')
    brand_color = models.CharField('Brand Primary Color', max_length=20, default='#6366f1')
    accent_color = models.CharField('Accent Color', max_length=20, default='#10b981')
    dark_mode = models.BooleanField('Dark Mode Default', default=True)
    public_base_url = models.URLField(
        'Public site URL', blank=True,
        help_text='The public address where this app is hosted (e.g. https://app.myagency.com). Used in portfolio/proposal links sent to clients. Links to localhost cannot be opened by clients.')
    portfolio_enabled = models.BooleanField('Show my public portfolio page', default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'User settings'

    def __str__(self):
        return f"Settings for {self.user.email}"

    # secrets are stored encrypted
    @property
    def smtp_password(self):
        return decrypt(self.smtp_password_enc)

    @smtp_password.setter
    def smtp_password(self, value):
        self.smtp_password_enc = encrypt(value)

    @property
    def gemini_api_key(self):
        return decrypt(self.gemini_api_key_enc)

    @gemini_api_key.setter
    def gemini_api_key(self, value):
        self.gemini_api_key_enc = encrypt(value)

    @property
    def smtp_ready(self):
        return bool(self.smtp_host and self.smtp_username and self.smtp_password_enc)

    @property
    def display_agency_name(self):
        return self.agency_name or self.user.full_name or self.user.username

    @property
    def get_logo(self):
        if self.logo_file:
            try:
                return self.logo_file.url
            except Exception:
                pass
        return self.logo_url or ''
