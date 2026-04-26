from django import forms
from events.models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model  = Event
        fields = [
            'title', 'description', 'date_time', 'end_time',
            'venue', 'capacity', 'category', 'image', 'requires_approval',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-ink-50 border border-ink-200 rounded-xl text-sm text-ink-800 placeholder-ink-300 focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all font-medium',
                'placeholder': 'Enter event title...'
            }),
            'date_time': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={
                    'type': 'datetime-local',
                    'class': 'w-full px-4 py-3 bg-ink-50 border border-ink-200 rounded-xl text-sm text-ink-800 focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all'
                }
            ),
            'end_time':  forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={
                    'type': 'datetime-local',
                    'class': 'w-full px-4 py-3 bg-ink-50 border border-ink-200 rounded-xl text-sm text-ink-800 focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all'
                }
            ),
            'venue': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-ink-50 border border-ink-200 rounded-xl text-sm text-ink-800 placeholder-ink-300 focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all',
                'placeholder': 'Where is it happening?'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-ink-50 border border-ink-200 rounded-xl text-sm text-ink-800 placeholder-ink-300 focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all',
                'placeholder': 'Max attendees'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-ink-50 border border-ink-200 rounded-xl text-sm text-ink-800 focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all'
            }),
            'requires_approval': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-brand bg-slate-100 border-slate-300 rounded focus:ring-brand focus:ring-2 cursor-pointer'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 bg-ink-50 border border-ink-200 rounded-xl text-sm text-ink-800 placeholder-ink-300 focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all',
                'placeholder': 'Share some details about the event...'
            }),
        }