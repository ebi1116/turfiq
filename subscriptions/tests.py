from django.contrib.auth.models import User
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import hashlib
import hmac
import json
from unittest.mock import patch

from .models import Subscription


class PremiumAccessTests(TestCase):
    def test_regular_owner_without_subscription_starts_free_trial(self):
        user = User.objects.create_user("free-owner", password="password")
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(owner=user)
        self.assertEqual(subscription.status, "trialing")
        self.assertTrue(subscription.has_access)

    def test_expired_trial_owner_is_sent_to_billing_when_opening_booking(self):
        user = User.objects.create_user("saving-owner", password="password")
        Subscription.objects.create(owner=user, status="trialing", trial_end=timezone.now() - timedelta(seconds=1))
        self.client.force_login(user)
        response = self.client.get(reverse("booking-add"))
        self.assertRedirects(response, reverse("billing"))

    def test_new_owner_receives_free_trial_and_can_create_bookings(self):
        user = User.objects.create_user("new-owner", email="new-owner@example.com", password="password")
        self.client.force_login(user)
        response = self.client.post(reverse("customer-add"), {"name": "Free Customer", "phone": "888"})
        self.assertRedirects(response, reverse("customer-list"))
        self.assertEqual(self.client.get(reverse("booking-add")).status_code, 200)
        subscription = Subscription.objects.get(owner=user)
        self.assertEqual(subscription.status, "trialing")
        self.assertTrue(subscription.has_access)
        self.assertAlmostEqual((subscription.trial_end - subscription.trial_start).total_seconds(), 30 * 86400, delta=2)

    def test_one_owners_payment_does_not_activate_another_email(self):
        paid = User.objects.create_user("paid", email="paid@example.com", password="password")
        unpaid = User.objects.create_user("unpaid", email="unpaid@example.com", password="password")
        Subscription.objects.create(owner=paid, status="active")
        self.client.force_login(unpaid)

        response = self.client.get(reverse("booking-list"))

        self.assertEqual(response.status_code, 200)
        unpaid_subscription = Subscription.objects.get(owner=unpaid)
        self.assertEqual(unpaid_subscription.status, "trialing")
        self.assertNotEqual(unpaid_subscription.status, "active")

    def test_active_owner_can_open_dashboard(self):
        user = User.objects.create_user("premium-owner", password="password")
        Subscription.objects.create(owner=user, status="active")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_superuser_bypasses_billing(self):
        user = User.objects.create_superuser("premium-root", "root@example.com", "password")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_admin_login_is_not_blocked_by_billing(self):
        user = User.objects.create_user("expired-owner", password="password")
        Subscription.objects.create(owner=user, status="trialing", trial_end=timezone.now() - timedelta(seconds=1))
        self.client.force_login(user)

        response = self.client.post(reverse("admin:login"), {"username": user.username, "password": "password"})

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.get("Location"), reverse("billing"))

    def test_billing_page_shows_monthly_price(self):
        user = User.objects.create_user("billing-owner", password="password")
        self.client.force_login(user)
        response = self.client.get(reverse("billing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "199")

    @override_settings(RAZORPAY_KEY_ID="rzp_test_public", RAZORPAY_KEY_SECRET="test-secret")
    def test_billing_page_uses_standard_checkout_not_legacy_autopay(self):
        user = User.objects.create_user("standard-billing-owner", password="password")
        Subscription.objects.create(
            owner=user,
            status="trialing",
            trial_end=timezone.now() - timedelta(seconds=1),
        )
        self.client.force_login(user)
        response = self.client.get(reverse("billing"))
        self.assertContains(response, 'id="razorpay-pay-button"')
        self.assertNotContains(response, "Authorize &amp; Start Trial")
        self.assertNotContains(response, "subscription_id")
        self.assertContains(response, reverse("create-order"))
        self.assertContains(response, reverse("verify-payment"))
        self.assertIn("csrftoken", response.cookies)

    @override_settings(TEST_ACCOUNT_EMAIL="demo@turfiq.local")
    def test_configured_test_account_bypasses_premium_and_billing(self):
        user = User.objects.create_user("demo", "demo@turfiq.local", "password")
        Subscription.objects.create(owner=user, status="trialing", trial_end=timezone.now() - timedelta(seconds=1))
        self.client.force_login(user)

        response = self.client.post(reverse("customer-add"), {"name": "Demo Customer", "phone": "777"})

        self.assertRedirects(response, reverse("customer-list"))
        self.assertRedirects(self.client.get(reverse("billing")), reverse("dashboard"))


@override_settings(RAZORPAY_KEY_ID="rzp_test_public", RAZORPAY_KEY_SECRET="test-secret")
class StandardCheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("checkout-owner", password="password")
        self.client.force_login(self.user)

    @patch("subscriptions.views.create_razorpay_order")
    def test_create_order_ignores_client_amount_and_uses_monthly_price(self, create):
        create.return_value = {"id": "order_test", "amount": 19900, "currency": "INR"}
        response = self.client.post(
            reverse("create-order"),
            json.dumps({"amount": 99, "currency": "INR"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        create.assert_called_once_with(19900, "INR", create.call_args.args[2])

    @patch("subscriptions.views.create_razorpay_order")
    def test_create_order_returns_checkout_fields_and_stores_pending_order(self, create):
        create.return_value = {"id": "order_test", "amount": 19900, "currency": "INR"}
        response = self.client.post(
            reverse("create-order"),
            json.dumps({"amount": 19900, "currency": "INR"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"order_id": "order_test", "amount": 19900, "currency": "INR"})
        self.assertEqual(self.client.session["razorpay_pending_order"]["id"], "order_test")
        self.assertEqual(self.client.session["razorpay_pending_order"]["purpose"], "premium")

    def test_verify_payment_rejects_missing_fields(self):
        response = self.client.post(reverse("verify-payment"), "{}", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_verify_payment_rejects_signature_mismatch_without_activating(self):
        session = self.client.session
        session["razorpay_pending_order"] = {"id": "order_test", "amount": 19900, "currency": "INR", "purpose": "premium"}
        session.save()
        response = self.client.post(
            reverse("verify-payment"),
            json.dumps({"razorpay_order_id": "order_test", "razorpay_payment_id": "pay_test", "razorpay_signature": "invalid"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Subscription.objects.filter(owner=self.user, status="active").exists())

    def test_verify_payment_accepts_valid_signature_and_activates_premium(self):
        session = self.client.session
        session["razorpay_pending_order"] = {"id": "order_test", "amount": 19900, "currency": "INR", "purpose": "premium"}
        session.save()
        signature = hmac.new(b"test-secret", b"order_test|pay_test", hashlib.sha256).hexdigest()
        response = self.client.post(
            reverse("verify-payment"),
            json.dumps({"razorpay_order_id": "order_test", "razorpay_payment_id": "pay_test", "razorpay_signature": signature}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(owner=self.user)
        self.assertEqual(subscription.status, "active")
        self.assertEqual(subscription.razorpay_payment_id, "pay_test")
        self.assertAlmostEqual((subscription.current_end - subscription.current_start).total_seconds(), 30 * 86400, delta=2)

    @patch("subscriptions.views.create_razorpay_order")
    def test_expired_paid_trial_uses_monthly_price(self, create):
        Subscription.objects.create(
            owner=self.user,
            status="trialing",
            razorpay_payment_id="pay_trial",
            trial_end=timezone.now() - timedelta(seconds=1),
        )
        create.return_value = {"id": "order_renew", "amount": 19900, "currency": "INR"}
        response = self.client.post(reverse("create-order"), json.dumps({"currency": "INR"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["amount"], 19900)
        self.assertEqual(self.client.session["razorpay_pending_order"]["purpose"], "premium")
