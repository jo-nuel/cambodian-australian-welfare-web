from django import forms


class ContactForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Full name"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Phone number"}),
    )
    enquiry_area = forms.ChoiceField(
        choices=[
            ("", "Select an area of enquiry"),
            ("general", "General enquiry"),
            ("programs", "Programs and services"),
            ("referrals", "Referrals and support"),
            ("partnerships", "Partnerships"),
            ("volunteering", "Volunteering"),
            ("events", "Events"),
        ],
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 7,
                "placeholder": "Tell us how we can help",
            }
        ),
    )
