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
        for name in ("business_name", "number_of_grounds"):
            self.fields[name].required = True
        for name in ("owner_name", "phone_number", "address", "logo"):
            self.fields[name].required = False
        self.fields["number_of_grounds"].widget.attrs.update({"min": 1, "max": 50})

    def clean_number_of_grounds(self):
        value = self.cleaned_data["number_of_grounds"]
        if not 1 <= value <= 50:
            raise forms.ValidationError("Enter a number between 1 and 50.")
        return value


class TurfOnboardingForm(forms.Form):
    number_of_grounds = forms.IntegerField(
        min_value=1, max_value=50, label="How many turfs do you have?",
        widget=forms.NumberInput(attrs={"min": 1, "max": 50}),
    )

    def clean(self):
        cleaned = super().clean()
        count = cleaned.get("number_of_grounds")
        if count:
            names = []
            for number in range(1, count + 1):
                name = self.data.get(f"turf_name_{number}", "").strip()
                if not name:
                    self.add_error(None, f"Turf {number} name is required.")
                names.append(name)
            cleaned["turf_names"] = names
        return cleaned
