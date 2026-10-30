from django import forms
from django.core.files.uploadedfile import UploadedFile
from .models import PortfolioItem, PortfolioFAQ, PortfolioTestimonial

INPUT = ('w-full px-4 py-2.5 rounded-2xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 text-sm '
         'placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition shadow-sm')


class PortfolioItemForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = ['title', 'client_name', 'industry', 'badge_text', 'technologies', 'results',
                  'live_url', 'image', 'image_url', 'description',
                  'testimonial', 'testimonial_author', 'sort_order', 'is_published']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'h-4 w-4 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500'
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = ('block w-full text-sm text-slate-600 dark:text-slate-400 file:mr-4 file:py-2.5 file:px-4 '
                                               'file:rounded-xl file:border-0 file:text-xs file:font-bold '
                                               'file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 shadow-sm')
                field.widget.attrs['accept'] = 'image/*'
            else:
                field.widget.attrs['class'] = INPUT
                if isinstance(field.widget, forms.Textarea):
                    field.widget.attrs['rows'] = 3

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if isinstance(image, UploadedFile):  # only validate a NEW upload
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                raise forms.ValidationError('Please upload a PNG, JPG, WEBP or GIF image.')
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image is too large (max 5 MB).')
        return image


class PortfolioFAQForm(forms.ModelForm):
    class Meta:
        model = PortfolioFAQ
        fields = ['question', 'answer', 'sort_order', 'is_published']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'h-4 w-4 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500'
            else:
                field.widget.attrs['class'] = INPUT
                if isinstance(field.widget, forms.Textarea):
                    field.widget.attrs['rows'] = 3


class PortfolioTestimonialForm(forms.ModelForm):
    class Meta:
        model = PortfolioTestimonial
        fields = ['client_name', 'client_role', 'company_name', 'rating', 'project_title', 'feedback', 'avatar_url', 'sort_order', 'is_published']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'h-4 w-4 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 focus:ring-indigo-500'
            else:
                field.widget.attrs['class'] = INPUT
                if isinstance(field.widget, forms.Textarea):
                    field.widget.attrs['rows'] = 3

