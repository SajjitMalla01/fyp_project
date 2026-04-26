from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role  = forms.ChoiceField(
        choices=[
            ('STUDENT', 'Student'),
            ('STAFF',   'Staff'),
        ],
        help_text='Admins are created by existing admins only.'
    )
    college = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select your College manually..."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from tenants.models import College
        self.fields['college'].queryset = College.objects.filter(status__in=['ACTIVE'])
        self.fields['college'].widget.attrs.update({
            'class': 'w-full px-4 py-3 bg-ink-50 border border-ink-200 rounded-xl text-sm text-ink-800 focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all'
        })

    class Meta:
        model  = User
        fields = ['username', 'email', 'role', 'college', 'password1', 'password2']