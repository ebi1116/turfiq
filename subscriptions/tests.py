from django.contrib.auth.models import User
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import Subscription


class PremiumAccessTests(TestCase):
    def test_regular_owner_without_subscription_can_open_dashboard_onboarding(self):
        user = User.objects.create_user("free-owner", password="password")
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HOW TURFIQ WORKS")

    def test_expired_trial_owner_is_sent_to_billing_when_opening_booking(self):
        user = User.objects.create_user("saving-owner", password="password")
        Subscription.objects.create(owner=user, status="trialing", trial_end=timezone.now() - timedelta(seconds=1))
        self.client.force_login(user)
        response = self.client.get(reverse("booking-add"))
        self.assertRedirects(response, reverse("billing"))

    def test_new_owner_can_add_customer_but_booking_requires_premium(self):
        user = User.objects.create_user("new-owner", email="new-owner@example.com", password="password")
        self.client.force_login(user)
        response = self.client.post(reverse("customer-add"), {"name": "Free Customer", "phone": "888"})
        self.assertRedirects(response, reverse("customer-list"))
        self.assertRedirects(self.client.get(reverse("booking-add")), reverse("billing"))
        subscription = Subscription.objects.get(owner=user)
        self.assertEqual(subscription.status, "inactive")
        self.assertFalse(subscription.has_access)

    def test_one_owners_payment_does_not_unlock_another_email(self):
        paid = User.objects.create_user("paid", email="paid@example.com", password="password")
        unpaid = User.objects.create_user("unpaid", email="unpaid@example.com", password="password")
        Subscription.objects.create(owner=paid, status="active")
        self.client.force_login(unpaid)

        response = self.client.get(reverse("booking-list"))

        self.assertRedirects(response, reverse("billing"))
        self.assertFalse(Subscription.objects.get(owner=unpaid).has_access)

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

    @override_settings(TEST_ACCOUNT_EMAIL="demo@turfiq.local")
    def test_configured_test_account_bypasses_premium_and_billing(self):
        user = User.objects.create_user("demo", "demo@turfiq.local", "password")
        Subscription.objects.create(owner=user, status="trialing", trial_end=timezone.now() - timedelta(seconds=1))
        self.client.force_login(user)

        response = self.client.post(reverse("customer-add"), {"name": "Demo Customer", "phone": "777"})

        self.assertRedirects(response, reverse("customer-list"))
        self.assertRedirects(self.client.get(reverse("billing")), reverse("dashboard"))
