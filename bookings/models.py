from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from business.models import Ground

class Customer(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customers")
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["owner", "phone"], name="unique_owner_customer_phone")]
        ordering = ["name"]
    def __str__(self): return f"{self.name} — {self.phone}"

class Booking(models.Model):
    SPORTS = [(x, x) for x in ("Football", "Cricket", "Badminton", "Other")]
    PAYMENTS = [(x, x) for x in ("UPI", "Cash", "Card", "Online")]
    STATUSES = [(x, x) for x in ("Confirmed", "Completed", "Cancelled", "Pending")]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="bookings")
    booking_date = models.DateField(db_index=True)
    booking_time = models.TimeField()
    duration = models.DecimalField(max_digits=4, decimal_places=1, help_text="Duration in hours")
    sport = models.CharField(max_length=20, choices=SPORTS)
    ground = models.ForeignKey(Ground, on_delete=models.PROTECT, related_name="bookings")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENTS)
    status = models.CharField(max_length=20, choices=STATUSES, default="Confirmed")
    is_paid = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def clean(self):
        errors = {}
        if self.customer_id and self.owner_id and self.customer.owner_id != self.owner_id:
            errors["customer"] = "Customer must belong to the booking owner."
        if self.ground_id and self.owner_id and self.ground.owner_id != self.owner_id:
            errors["ground"] = "Ground must belong to the booking owner."
        if errors:
            raise ValidationError(errors)
    class Meta: ordering = ["-booking_date", "-booking_time"]
    def __str__(self): return f"{self.customer} — {self.booking_date}"


class BlockedSlot(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocked_slots")
    ground = models.ForeignKey(Ground, on_delete=models.CASCADE, related_name="blocked_slots")
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(db_index=True)
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("start_at",)
        constraints = [models.CheckConstraint(condition=Q(end_at__gt=models.F("start_at")), name="blocked_slot_positive_duration")]

    def clean(self):
        errors = {}
        if self.ground_id and self.owner_id and self.ground.owner_id != self.owner_id:
            errors["ground"] = "Ground must belong to the blocked slot owner."
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            errors["end_at"] = "End time must be after start time."
        if errors:
            raise ValidationError(errors)
