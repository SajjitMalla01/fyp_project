from django import forms
from .models import College


class CollegeRegistrationForm(forms.ModelForm):
    class Meta:
        model = College
        fields = ['name', 'slug', 'email', 'phone', 'address', 'website',
                  'primary_color', 'accent_color']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
        }
