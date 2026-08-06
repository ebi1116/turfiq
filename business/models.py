from django.contrib.auth.models import User
from django.db import models
from datetime import time

class BusinessSettings(models.Model):
    CURRENCIES = [("₹", "INR (₹)"), ("$", "USD ($)"), ("€", "EUR (€)"), ("£", "GBP (£)")]
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="business_settings")
    business_name = models.CharField(max_length=120, default="My Turf")
    logo = models.ImageField(upload_to="logos/", blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default="₹")
    timezone = models.CharField(max_length=60, default="Asia/Kolkata")
    opening_time = models.TimeField(default=time(6, 0))
    closing_time = models.TimeField(default=time(23, 0))
    monthly_revenue_goal = models.DecimalField(max_digits=12, decimal_places=2, default=100000)
    def __str__(self): return self.business_name


class TurfOwnerWorkspace(User):
    """Admin-only proxy used as a folder-style tenant directory."""

    class Meta:
        proxy = True
        verbose_name = "Turf owner folder"
        verbose_name_plural = "Turf owner folders"
