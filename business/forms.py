from django import forms
from .models import BusinessSettings
class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        fields = ("business_name", "owner_name", "phone_number", "address", "number_of_grounds", "logo", "currency", "timezone", "opening_time", "closing_time", "monthly_revenue_goal")
        labels = {"business_name": "Turf name", "owner_name": "Turf owner name", "address": "Address / location"}
        widgets = {"opening_time": forms.TimeInput(attrs={"type":"time"}), "closing_time": forms.TimeInput(attrs={"type":"time"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("business_name", "owner_name", "phone_number", "number_of_grounds"):
            self.fields[name].required = True
        self.fields["number_of_grounds"].widget.attrs.update({"min": 1, "max": 50})

    def clean_number_of_grounds(self):
        value = self.cleaned_data["number_of_grounds"]
        if not 1 <= value <= 50:
            raise forms.ValidationError("Enter a number between 1 and 50.")
        return value
