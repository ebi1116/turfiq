from django import forms
from django.db.models import Q
from .models import Booking, Customer
from business.models import Ground


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
        self._user = user
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(owner=user).order_by("name") if user else Customer.objects.none()
        self.fields["customer"].empty_label = "Select a customer"
        if user:
            allowed = Q(is_active=True)
            if self.instance and self.instance.pk and self.instance.ground_id:
                allowed |= Q(pk=self.instance.ground_id)
            self.fields["ground"].queryset = Ground.objects.filter(Q(owner=user) & allowed).order_by("number")
        else:
            self.fields["ground"].queryset = Ground.objects.none()
        self.fields["ground"].empty_label = "Select a ground"

    def clean_ground(self):
        ground = self.cleaned_data["ground"]
        if self._user and ground.owner_id != self._user.id:
            raise forms.ValidationError("Select one of your own grounds.")
        return ground
