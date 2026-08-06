from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import Subscription


class PremiumAccessTests(TestCase):
    def test_regular_owner_without_subscription_can_explore_dashboard(self):
        user = User.objects.create_user("free-owner", password="password")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_expired_trial_owner_is_sent_to_billing_when_saving(self):
        user = User.objects.create_user("saving-owner", password="password")
        Subscription.objects.create(owner=user, status="trialing", trial_end=timezone.now() - timedelta(seconds=1))
        self.client.force_login(user)
        response = self.client.post(reverse("customer-add"), {"name": "Blocked", "phone": "999"})
        self.assertRedirects(response, reverse("billing"))

    def test_new_owner_gets_seven_day_trial_and_can_save(self):
        user = User.objects.create_user("trial-owner", password="password")
        self.client.force_login(user)
        response = self.client.post(reverse("customer-add"), {"name": "Trial Customer", "phone": "888"})
        self.assertRedirects(response, reverse("customer-list"))
        subscription = Subscription.objects.get(owner=user)
        self.assertTrue(subscription.is_trialing)
        self.assertGreater(subscription.trial_end, timezone.now() + timedelta(days=6))

    def test_active_owner_can_open_dashboard(self):
        user = User.objects.create_user("premium-owner", password="password")
        Subscription.objects.create(owner=user, status="active")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_superuser_bypasses_billing(self):
        user = User.objects.create_superuser("premium-root", "root@example.com", "password")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_billing_page_shows_monthly_price(self):
        user = User.objects.create_user("billing-owner", password="password")
        self.client.force_login(user)
        response = self.client.get(reverse("billing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "199")
