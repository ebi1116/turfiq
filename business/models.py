from django.contrib.auth.models import User
from django.db import models
from datetime import time

class BusinessSettings(models.Model):
    CURRENCIES = [("₹", "INR (₹)"), ("$", "USD ($)"), ("€", "EUR (€)"), ("£", "GBP (£)")]
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="business_settings")
    business_name = models.CharField(max_length=120, default="My Turf")
    owner_name = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    number_of_grounds = models.PositiveIntegerField(default=1)
    logo = models.ImageField(upload_to="logos/", blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default="₹")
    timezone = models.CharField(max_length=60, default="Asia/Kolkata")
    opening_time = models.TimeField(default=time(6, 0))
    closing_time = models.TimeField(default=time(23, 0))
    monthly_revenue_goal = models.DecimalField(max_digits=12, decimal_places=2, default=100000)
    onboarding_completed = models.BooleanField(default=False)
    def __str__(self): return self.business_name


class Ground(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="grounds")
    turf = models.ForeignKey(BusinessSettings, on_delete=models.CASCADE, related_name="grounds")
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    use_custom_hours = models.BooleanField(default=False)
    is_24_hours = models.BooleanField(default=False)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("number",)
        constraints = [models.UniqueConstraint(fields=("turf", "number"), name="unique_turf_ground_number")]

    @property
    def display_name(self):
        return self.name.strip() or f"Ground {self.number}"

    def __str__(self):
        return self.display_name


class TurfOwnerWorkspace(User):
    """Admin-only proxy used as a folder-style tenant directory."""

    class Meta:
        proxy = True
        verbose_name = "Turf owner folder"
        verbose_name_plural = "Turf owner folders"
