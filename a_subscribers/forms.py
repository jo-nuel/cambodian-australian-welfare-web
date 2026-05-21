from django import forms

from .models import Subscriber


class SubscriptionForm(forms.Form):
    email = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={
            'placeholder': 'your@email.com',
            'autocomplete': 'email',
        }),
    )
    language_preference = forms.ChoiceField(
        label='Preferred language',
        choices=Subscriber.LANGUAGE_CHOICES,
        initial=Subscriber.LANGUAGE_ANY,
        required=False,
    )
    # Honeypot — hidden from real users via CSS; bots fill it in
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Bot detected.')
        return ''

    def clean_email(self):
        return self.cleaned_data['email'].lower().strip()
