import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import Subscription, WebhookEvent
from .access import is_test_account
from .services import (
    RazorpayAuthError, RazorpayError, create_razorpay_order,
    timestamp, verify_checkout_signature, verify_order_signature,
    verify_webhook_signature,
)


@login_required
@ensure_csrf_cookie
def billing(request):
    if request.user.is_superuser or is_test_account(request.user):
        return redirect("dashboard")
    subscription, _ = Subscription.objects.get_or_create(owner=request.user)
    return render(request, "subscriptions/billing.html", {
        "subscription": subscription,
        "price": settings.PREMIUM_MONTHLY_PRICE,
        "standard_checkout_configured": all((settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)),
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    })


def _json_body(request):
    try:
        return json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


@login_required
@require_POST
def create_order(request):
    payload = _json_body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)
    amount = payload.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount < 100:
        return JsonResponse({"error": "Amount must be an integer of at least 100 paise."}, status=400)
    expected_amount = settings.PREMIUM_MONTHLY_PRICE * 100
    if amount != expected_amount:
        return JsonResponse({"error": f"Premium checkout amount must be {expected_amount} paise."}, status=400)
    currency = str(payload.get("currency", "INR")).upper()
    if currency != "INR":
        return JsonResponse({"error": "Only INR is supported."}, status=400)
    receipt = f"turfiq-{request.user.pk}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    try:
        order = create_razorpay_order(amount, currency, receipt)
    except RazorpayAuthError as exc:
        return JsonResponse({"error": str(exc)}, status=401)
    except RazorpayError:
        return JsonResponse({"error": "Unable to create a Razorpay order. Please try again."}, status=500)
    request.session["razorpay_pending_order"] = {
        "id": order["id"], "amount": order["amount"], "currency": order["currency"],
    }
    return JsonResponse({"order_id": order["id"], "amount": order["amount"], "currency": order["currency"]})


@login_required
@require_POST
def verify_payment(request):
    payload = _json_body(request)
    required = ("razorpay_payment_id", "razorpay_order_id", "razorpay_signature")
    if payload is None or any(not payload.get(field) for field in required):
        return JsonResponse({"success": False, "error": "Missing payment verification fields."}, status=400)
    pending = request.session.get("razorpay_pending_order", {})
    if payload["razorpay_order_id"] != pending.get("id"):
        return JsonResponse({"success": False, "error": "Payment order does not match this checkout."}, status=400)
    if not verify_order_signature(payload["razorpay_order_id"], payload["razorpay_payment_id"], payload["razorpay_signature"]):
        return JsonResponse({"success": False, "error": "Invalid payment signature."}, status=400)
    subscription, _ = Subscription.objects.get_or_create(owner=request.user)
    subscription.razorpay_payment_id = payload["razorpay_payment_id"]
    subscription.status = "active"
    subscription.current_start = timezone.now()
    subscription.current_end = subscription.current_start + timedelta(days=30)
    subscription.save(update_fields=["razorpay_payment_id", "status", "current_start", "current_end", "updated_at"])
    request.session.pop("razorpay_pending_order", None)
    return JsonResponse({"success": True, "redirect": request.session.pop("premium_return_to", "/dashboard/")})


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
