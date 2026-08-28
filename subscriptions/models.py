from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta


def default_trial_end():
    return timezone.now() + timedelta(days=30)


class Subscription(models.Model):
    ACTIVE_STATUSES = {"authenticated", "active"}
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="premium_subscription")
    razorpay_subscription_id = models.CharField(max_length=80, unique=True, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=80, blank=True)
    razorpay_plan_id = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=30, default="trialing", db_index=True)
    trial_start = models.DateTimeField(default=timezone.now)
    trial_end = models.DateTimeField(default=default_trial_end)
    current_start = models.DateTimeField(null=True, blank=True)
    current_end = models.DateTimeField(null=True, blank=True)
    cancel_at_cycle_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def has_access(self):
        if self.status == "trialing":
            return self.trial_end >= timezone.now()
        if self.status not in self.ACTIVE_STATUSES:
            return False
        return not self.current_end or self.current_end >= timezone.now()

    @property
    def is_trialing(self):
        return self.status == "trialing" and self.trial_end >= timezone.now()

    def __str__(self):
        return f"{self.owner} — {self.status}"


class WebhookEvent(models.Model):
    event_id = models.CharField(max_length=100, unique=True)
    event_type = models.CharField(max_length=80)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_type
