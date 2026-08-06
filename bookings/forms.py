from django import forms
from .models import Booking, Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ("name", "phone", "email")


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = (
            "customer", "booking_date", "booking_time", "duration", "sport",
            "ground", "amount", "payment_method", "status", "is_paid", "notes",
        )
        widgets = {"booking_date": forms.DateInput(attrs={"type":"date"}), "booking_time": forms.TimeInput(attrs={"type":"time"}), "notes": forms.Textarea(attrs={"rows":3})}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(owner=user).order_by("name") if user else Customer.objects.none()
        self.fields["customer"].empty_label = "Select a customer"
