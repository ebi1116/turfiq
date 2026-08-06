import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.conf import settings


class RazorpayError(Exception):
    pass


def create_razorpay_subscription(owner, trial_end=None):
    if not all((settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET, settings.RAZORPAY_PLAN_ID)):
        raise RazorpayError("Razorpay is not configured. Add the API key, secret and monthly plan ID.")
    subscription_data = {
        "plan_id": settings.RAZORPAY_PLAN_ID,
        "total_count": 120,
        "quantity": 1,
        "customer_notify": True,
        "notes": {"turfiq_owner_id": str(owner.pk), "email": owner.email},
    }
    if trial_end and trial_end.timestamp() > datetime.now(tz=timezone.utc).timestamp() + 60:
        subscription_data["start_at"] = int(trial_end.timestamp())
    payload = json.dumps(subscription_data).encode()
    token = base64.b64encode(f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()).decode()
    request = Request("https://api.razorpay.com/v1/subscriptions", data=payload, headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        try: detail = json.loads(exc.read()).get("error", {}).get("description", "Razorpay rejected the request.")
        except (ValueError, AttributeError): detail = "Razorpay rejected the request."
        raise RazorpayError(detail) from exc


def verify_checkout_signature(payment_id, subscription_id, signature):
    message = f"{payment_id}|{subscription_id}".encode()
    expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(raw_body, signature):
    expected = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def timestamp(value):
    return datetime.fromtimestamp(value, tz=timezone.utc) if value else None
