from django.test import TestCase
from django.core import mail
from django.urls import reverse

from .models import ContactMessage


class MarketingSiteTests(TestCase):
    def test_public_pages_render(self):
        for name in ("home", "about", "contact", "faq", "privacy", "terms", "refund-policy", "shipping-policy"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_home_contains_seo_and_primary_cta(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Know your business")
        self.assertContains(response, "About BIZ IQ")
        self.assertContains(response, "Terms & Conditions")
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'property="og:title"')

    def test_contact_form_stores_message(self):
        response = self.client.post(reverse("contact"), {"name": "Owner", "email": "owner@example.com", "phone": "9876543210", "subject": "Analytics question", "message": "Please help with my dashboard."})
        self.assertRedirects(response, reverse("contact-thank-you"))
        self.assertTrue(ContactMessage.objects.filter(email="owner@example.com").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["support@turfiq.in"])
        self.assertEqual(mail.outbox[0].reply_to, ["owner@example.com"])

    def test_search_discovery_files(self):
        self.assertContains(self.client.get(reverse("robots-txt")), "Sitemap:")
        self.assertContains(self.client.get(reverse("sitemap")), "<urlset")

    def test_pwa_files_are_valid_and_service_worker_has_root_scope(self):
        manifest_response = self.client.get(reverse("webmanifest"))
        self.assertEqual(manifest_response["Content-Type"], "application/manifest+json")
        manifest = manifest_response.json()
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["start_url"], "/dashboard/")
        self.assertGreaterEqual(len(manifest["icons"]), 2)

        worker = self.client.get(reverse("service-worker"))
        self.assertEqual(worker.status_code, 200)
        self.assertEqual(worker["Content-Type"], "application/javascript")
        self.assertEqual(worker["Service-Worker-Allowed"], "/")
        self.assertContains(worker, "OFFLINE_URL")
        self.assertEqual(self.client.get(reverse("offline")).status_code, 200)
