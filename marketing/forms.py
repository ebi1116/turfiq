from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "subject", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 5, "placeholder": "How can we help?"})}
