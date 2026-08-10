import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Subscription, WebhookEvent
from .access import is_test_account
from .services import RazorpayError, create_razorpay_subscription, timestamp, verify_checkout_signature, verify_webhook_signature


@login_required
def billing(request):
    if request.user.is_superuser or is_test_account(request.user):
        return redirect("dashboard")
    subscription, _ = Subscription.objects.get_or_create(owner=request.user)
    checkout = None
    if request.method == "POST":
        try:
            remote = create_razorpay_subscription(request.user, subscription.trial_end)
            subscription.razorpay_subscription_id = remote["id"]
            subscription.razorpay_plan_id = settings.RAZORPAY_PLAN_ID
            subscription.status = remote.get("status", "created")
            subscription.save()
            checkout = {"key": settings.RAZORPAY_KEY_ID, "subscription_id": remote["id"], "name": "TurfIQ Analytics", "description": "7-day trial, then ₹199/month with autopay", "email": request.user.email, "contact": ""}
        except RazorpayError as exc:
            messages.error(request, str(exc))
    return render(request, "subscriptions/billing.html", {"subscription": subscription, "checkout": checkout, "price": settings.PREMIUM_MONTHLY_PRICE, "configured": all((settings.RAZORPAY_PLAN_ID, settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))})


@login_required
@require_POST
def verify_checkout(request):
    try:
        payload = json.loads(request.body)
        subscription = Subscription.objects.get(owner=request.user, razorpay_subscription_id=payload["razorpay_subscription_id"])
        if not verify_checkout_signature(payload["razorpay_payment_id"], subscription.razorpay_subscription_id, payload["razorpay_signature"]):
            return JsonResponse({"ok": False, "error": "Invalid payment signature."}, status=400)
        subscription.razorpay_payment_id = payload["razorpay_payment_id"]
        subscription.status = "authenticated"
        subscription.current_end = subscription.trial_end
        subscription.save(update_fields=["razorpay_payment_id", "status", "current_end", "updated_at"])
        return JsonResponse({"ok": True, "redirect": request.session.pop("premium_return_to", "/")})
    except (json.JSONDecodeError, KeyError, Subscription.DoesNotExist):
        return JsonResponse({"ok": False, "error": "Invalid checkout response."}, status=400)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    signature = request.headers.get("X-Razorpay-Signature", "")
    event_id = request.headers.get("X-Razorpay-Event-Id", "")
    if not settings.RAZORPAY_WEBHOOK_SECRET or not verify_webhook_signature(request.body, signature):
        return HttpResponseBadRequest("Invalid signature")
    if event_id and WebhookEvent.objects.filter(event_id=event_id).exists():
        return HttpResponse(status=200)
    try:
        payload = json.loads(request.body)
        entity = payload["payload"]["subscription"]["entity"]
        subscription = Subscription.objects.get(razorpay_subscription_id=entity["id"])
    except (json.JSONDecodeError, KeyError, Subscription.DoesNotExist):
        return HttpResponse(status=200)
    subscription.status = entity.get("status", subscription.status)
    remote_start = timestamp(entity.get("current_start"))
    remote_end = timestamp(entity.get("current_end"))
    if remote_start:
        subscription.current_start = remote_start
    if remote_end:
        subscription.current_end = remote_end
    elif subscription.status == "authenticated":
        subscription.current_end = subscription.trial_end
    subscription.cancel_at_cycle_end = bool(entity.get("has_scheduled_changes"))
    subscription.save()
    if event_id:
        WebhookEvent.objects.get_or_create(event_id=event_id, defaults={"event_type": payload.get("event", "unknown")})
    return HttpResponse(status=200)
