from django import forms


class GetInvolvedForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={'placeholder': 'Your full name'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone number (optional)'}),
    )
    interest = forms.ChoiceField(
        choices=[
            ('', 'Select an area of interest'),
            ('volunteering', 'Volunteering'),
            ('internship', 'Internship'),
            ('other', 'Other'),
        ],
    )
    availability = forms.ChoiceField(
        choices=[
            ('', 'Select your availability'),
            ('weekdays', 'Weekdays'),
            ('weekends', 'Weekends'),
            ('flexible', 'Flexible'),
        ],
    )
    skills = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Briefly describe any relevant skills or experience (optional)',
        }),
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Any additional information you would like to share (optional)',
        }),
    )
