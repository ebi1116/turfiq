from django.contrib import admin
from .models import Subscription, WebhookEvent


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("owner", "status", "trial_end", "razorpay_subscription_id", "current_end", "updated_at")
    list_filter = ("status", "cancel_at_cycle_end")
    search_fields = ("owner__username", "owner__email", "razorpay_subscription_id", "razorpay_payment_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "event_id", "received_at")
    readonly_fields = ("event_type", "event_id", "received_at")
