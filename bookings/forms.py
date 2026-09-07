from django import forms
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Booking, Customer
from business.models import Ground


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ("name", "phone", "email")
        labels = {"name": "Customer or Team name", "phone": "Mobile number (optional)"}

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if self._user and Customer.objects.filter(owner=self._user, name__iexact=name).exists():
            raise forms.ValidationError("This customer or team already exists.")
        return name


class BookingForm(forms.ModelForm):
    customer_name = forms.CharField(max_length=120, label="Customer or Team name", widget=forms.TextInput(attrs={"autocomplete": "off", "role": "combobox", "aria-autocomplete": "list", "aria-controls": "customerSuggestions"}))
    customer_phone = forms.CharField(max_length=20, required=False, label="Mobile number (optional)")
    ground = forms.CharField(
        label="Ground",
        widget=forms.TextInput(attrs={"list": "ground-options", "autocomplete": "off", "placeholder": "Type or select a ground"}),
    )

    class Meta:
        model = Booking
        fields = (
            "booking_date", "booking_time", "duration", "sport",
            "ground", "amount", "payment_method", "status", "is_paid", "notes",
        )
        widgets = {
            "booking_date": forms.DateInput(attrs={"type": "date"}),
            "booking_time": forms.TimeInput(attrs={"type": "time"}),
            "duration": forms.TextInput(attrs={"inputmode": "decimal", "list": "duration-options", "autocomplete": "off", "placeholder": "e.g. 1.5"}),
            "amount": forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off", "placeholder": "Enter amount"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        self._user = user
        super().__init__(*args, **kwargs)
        self.order_fields(("customer_name", "customer_phone", "booking_date", "booking_time", "duration", "sport", "ground", "amount", "payment_method", "status", "is_paid", "notes"))
        if self.instance and self.instance.pk and self.instance.customer_id:
            self.fields["customer_name"].initial = self.instance.customer.name
            self.fields["customer_phone"].initial = self.instance.customer.phone
        if user:
            allowed = Q(is_active=True)
            if self.instance and self.instance.pk and self.instance.ground_id:
                allowed |= Q(pk=self.instance.ground_id)
            self._grounds = list(Ground.objects.filter(Q(owner=user) & allowed).order_by("number"))
        else:
            self._grounds = []
        self.ground_options = [ground.display_name for ground in self._grounds]
        if not self.is_bound and self.instance and self.instance.pk and self.instance.ground_id:
            self.initial["ground"] = self.instance.ground.display_name

    def clean_ground(self):
        value = self.cleaned_data["ground"].strip()
        ground = next((item for item in self._grounds if str(item.pk) == value), None)
        if ground is None:
            ground = next((item for item in self._grounds if item.display_name.casefold() == value.casefold()), None)
        if ground is None:
            raise forms.ValidationError("Choose an existing ground from the suggestions.")
        return ground

    def clean_customer_name(self):
        return self.cleaned_data["customer_name"].strip()

    def clean_customer_phone(self):
        return self.cleaned_data["customer_phone"].strip()

    def clean(self):
        """Reject reservations that overlap an active reservation on a ground."""
        cleaned_data = super().clean()
        ground = cleaned_data.get("ground")
        booking_date = cleaned_data.get("booking_date")
        booking_time = cleaned_data.get("booking_time")
        duration = cleaned_data.get("duration")
        if not all((ground, booking_date, booking_time, duration)) or duration <= 0:
            return cleaned_data

        requested_start = datetime.combine(booking_date, booking_time)
        requested_end = requested_start + timedelta(hours=float(duration))
        candidates = Booking.objects.filter(
            owner=self._user, ground=ground,
            booking_date__range=(booking_date - timedelta(days=1), booking_date + timedelta(days=1)),
        ).exclude(status="Cancelled")
        if self.instance.pk:
            candidates = candidates.exclude(pk=self.instance.pk)
        for booking in candidates.only("booking_time", "duration"):
            existing_start = datetime.combine(booking.booking_date, booking.booking_time)
            existing_end = existing_start + timedelta(hours=float(booking.duration))
            if requested_start < existing_end and requested_end > existing_start:
                self.add_error("booking_time", "This turf is already booked for the selected time.")
                break
        return cleaned_data
