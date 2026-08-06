from django import forms
from .models import BusinessSettings
class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        exclude = ("owner",)
        widgets = {"opening_time": forms.TimeInput(attrs={"type":"time"}), "closing_time": forms.TimeInput(attrs={"type":"time"})}
