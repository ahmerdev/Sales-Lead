from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from .models import User, Workspace, UserSettings

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
        'placeholder': 'Create strong password'
    }))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
        'placeholder': 'Confirm password'
    }))

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
                'placeholder': 'Shahwaiz Khan'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
                'placeholder': 'you@company.com'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned_data


class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
        'placeholder': 'name@company.com'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
        'placeholder': '••••••••'
    }))


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'phone', 'avatar_url']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500',
            }),
            'avatar_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'https://...'
            }),
        }


# ==========================================================================
# Settings hub forms
# ==========================================================================
INPUT_CLASS = ('w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 text-sm '
               'placeholder-slate-400 dark:placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition shadow-sm')


class StyledFormMixin:
    """Gives every field the same dark Tailwind look."""
    def _style(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'h-4 w-4 rounded border-slate-600 bg-slate-950 text-indigo-600')
            else:
                field.widget.attrs.setdefault('class', INPUT_CLASS)
                if isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.setdefault('rows', 4)


class EmailSettingsForm(StyledFormMixin, forms.ModelForm):
    smtp_password = forms.CharField(
        label='SMTP password / App Password', required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password', 'placeholder': 'Leave empty to keep the saved password'}),
        help_text='Stored encrypted. Gmail/Outlook with 2-step verification need an App Password.')

    class Meta:
        model = UserSettings
        fields = ['smtp_host', 'smtp_port', 'smtp_security', 'smtp_username', 'smtp_password',
                  'from_name', 'from_email', 'reply_to', 'email_signature', 'email_footer']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields['email_signature'].widget.attrs['rows'] = 3
        self.fields['email_footer'].widget.attrs['rows'] = 2

    def save(self, commit=True):
        obj = super().save(commit=False)
        password = self.cleaned_data.get('smtp_password')
        if password:
            obj.smtp_password = password
        if commit:
            obj.save()
        return obj


class WhatsAppSettingsForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['whatsapp_number', 'default_country_code', 'whatsapp_default_message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()

    def clean_whatsapp_number(self):
        value = self.cleaned_data.get('whatsapp_number', '').strip()
        digits = ''.join(ch for ch in value if ch.isdigit())
        if value and len(digits) < 8:
            raise forms.ValidationError('Enter the full number with country code, e.g. +92 300 1234567.')
        return value


class ApiSettingsForm(StyledFormMixin, forms.Form):
    gemini_api_key = forms.CharField(
        label='Google Gemini API key', required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password', 'placeholder': 'Paste a new key to replace the saved one'}),
        help_text='Used to write AI pitches. Get a free key at aistudio.google.com. Stored encrypted.')
    clear_gemini = forms.BooleanField(label='Remove my saved Gemini key', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class AgencySettingsForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['agency_name', 'agency_tagline', 'agency_about', 'agency_website', 'logo_file', 'logo_url',
                  'font_family', 'brand_color', 'accent_color', 'dark_mode',
                  'public_base_url', 'portfolio_enabled']
        widgets = {
            'brand_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 p-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 cursor-pointer shadow-sm'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 p-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 cursor-pointer shadow-sm'}),
            'font_family': forms.Select(attrs={'class': 'w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm font-medium focus:ring-2 focus:ring-indigo-500 shadow-sm'}),
            'logo_file': forms.FileInput(attrs={'class': 'w-full text-xs text-slate-500 dark:text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-indigo-50 dark:file:bg-indigo-950 file:text-indigo-600 dark:file:text-indigo-400 hover:file:bg-indigo-100 cursor-pointer'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields['agency_about'].widget.attrs['rows'] = 4


class SuperAdminCreateUserForm(StyledFormMixin, forms.Form):
    full_name = forms.CharField(max_length=150, label='Full Name')
    email = forms.EmailField(label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput(), label='Temporary Password')
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='admin', label='Role')
    is_approved = forms.BooleanField(initial=True, required=False, label='Approve Immediately')
    is_superuser = forms.BooleanField(initial=False, required=False, label='Grant Super Admin Access')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email



class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class UserSMTPPasswordResetForm(PasswordResetForm):
    """
    Password-reset email. Sent through the user's OWN saved SMTP mailbox when they have one,
    otherwise through the project's default EMAIL_* settings (console by default in development).
    """
    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email,
                  html_email_template_name=None):
        from .services import get_user_settings, _connection, _from_header
        subject = ''.join(loader.render_to_string(subject_template_name, context).splitlines())
        body = loader.render_to_string(email_template_name, context)
        user = context.get('user')

        connection, sender = None, from_email
        if user is not None:
            s = get_user_settings(user)
            if s.smtp_ready:
                connection, sender = _connection(s), _from_header(user, s)

        try:
            EmailMultiAlternatives(subject, body, sender, [to_email], connection=connection).send()
        except Exception:
            if connection is None:
                raise
            # The user's own mailbox failed: fall back to the project's default email settings.
            EmailMultiAlternatives(subject, body, from_email, [to_email]).send(fail_silently=True)
