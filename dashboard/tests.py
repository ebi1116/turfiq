from datetime import date, time
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from bookings.models import Booking, Customer
from subscriptions.models import Subscription
from business.models import BusinessSettings, Ground

class DashboardTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user("owner",password="test-pass-123"); Subscription.objects.create(owner=self.user, status="active"); self.client.force_login(self.user)
        customer=Customer.objects.create(owner=self.user,name="Test Customer",phone="9000000000")
        turf=BusinessSettings.objects.create(owner=self.user); ground=Ground.objects.create(owner=self.user,turf=turf,number=1,name="A")
        Booking.objects.create(owner=self.user,customer=customer,booking_date=date.today(),booking_time=time(10),duration=1,sport="Football",ground=ground,amount=1000,payment_method="UPI",status="Completed")
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

    def test_profile_creates_and_safely_deactivates_grounds(self):
        payload = {"business_name":"Green Arena", "owner_name":"John", "phone_number":"9876543210", "address":"", "number_of_grounds":3,
                   "currency":self.user.business_settings.currency, "timezone":"Asia/Kolkata", "opening_time":"06:00", "closing_time":"23:00", "monthly_revenue_goal":"100000",
                   "ground_name_1":"Premier Arena", "ground_name_2":"", "ground_name_3":"Champions Ground"}
        self.client.post(reverse("profile"), payload)
        self.assertEqual(Ground.objects.filter(owner=self.user, is_active=True).count(), 3)
        self.assertEqual(Ground.objects.get(owner=self.user, number=1).display_name, "Premier Arena")
        self.assertEqual(Ground.objects.get(owner=self.user, number=2).display_name, "Ground 2")
        payload["number_of_grounds"] = 1
        self.client.post(reverse("profile"), payload)
        self.assertFalse(Ground.objects.get(owner=self.user, number=2).is_active)

    def test_ground_analytics_is_owner_scoped(self):
        other = User.objects.create_user("other-ground-owner", password="test-pass-123")
        other_turf = BusinessSettings.objects.create(owner=other)
        other_ground = Ground.objects.create(owner=other, turf=other_turf, number=1)
        self.assertEqual(self.client.get(reverse("ground-analytics", args=[other_ground.pk])).status_code, 404)
