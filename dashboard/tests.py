from datetime import date, time
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from bookings.models import Booking, Customer
from subscriptions.models import Subscription

class DashboardTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user("owner",password="test-pass-123"); Subscription.objects.create(owner=self.user, status="active"); self.client.force_login(self.user)
        customer=Customer.objects.create(owner=self.user,name="Test Customer",phone="9000000000")
        Booking.objects.create(owner=self.user,customer=customer,booking_date=date.today(),booking_time=time(10),duration=1,sport="Football",ground="A",amount=1000,payment_method="UPI",status="Completed")
    def test_dashboard_renders_metrics(self):
        response=self.client.get(reverse("dashboard")); self.assertEqual(response.status_code,200); self.assertContains(response,"Revenue"); self.assertContains(response,"Test Customer")
    def test_reports_and_crud_pages_render(self):
        for name in ("booking-list","expense-list","customer-list","reports","settings","profile"):
            self.assertEqual(self.client.get(reverse(name)).status_code,200,name)
    def test_csv_export(self):
        response=self.client.get(reverse("report-export",args=["csv"])); self.assertEqual(response.status_code,200); self.assertIn("text/csv",response["Content-Type"])

    def test_customer_can_be_added_and_selected_in_booking(self):
        response = self.client.post(reverse("customer-add"), {"name": "New Player", "phone": "9111111111", "email": "player@example.com"})
        self.assertRedirects(response, reverse("customer-list"))
        customer = Customer.objects.get(owner=self.user, phone="9111111111")
        response = self.client.get(reverse("booking-add"))
        self.assertContains(response, f"New Player — 9111111111")
        self.assertContains(response, f'value="{customer.pk}"')
