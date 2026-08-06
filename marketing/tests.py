from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage


class MarketingSiteTests(TestCase):
    def test_public_pages_render(self):
        for name in ("home", "about", "contact", "faq", "privacy", "terms", "refund-policy", "shipping-policy"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_home_contains_seo_and_primary_cta(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Know Your Turf")
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'property="og:title"')

    def test_contact_form_stores_message(self):
        response = self.client.post(reverse("contact"), {"name": "Owner", "email": "owner@example.com", "phone": "9876543210", "subject": "Analytics question", "message": "Please help with my dashboard."})
        self.assertRedirects(response, reverse("contact"))
        self.assertTrue(ContactMessage.objects.filter(email="owner@example.com").exists())

    def test_search_discovery_files(self):
        self.assertContains(self.client.get(reverse("robots-txt")), "Sitemap:")
        self.assertContains(self.client.get(reverse("sitemap")), "<urlset")
