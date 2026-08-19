from datetime import date, time, datetime, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from bookings.models import Booking, Customer, BlockedSlot
from dashboard.services import get_daily_booking_analytics
from django.utils import timezone
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

    def test_booking_accepts_manual_customer_and_stores_it(self):
        response = self.client.get(reverse("booking-add"))
        self.assertContains(response, "Customer or Team name")
        self.assertContains(response, "Mobile number (optional)")
        ground = Ground.objects.get(owner=self.user)
        response = self.client.post(reverse("booking-add"), {
            "customer_name": "Weekend Warriors", "customer_phone": "",
            "booking_date": date.today(), "booking_time": "12:00", "duration": "1",
            "sport": "Football", "ground": ground.pk, "amount": "500",
            "payment_method": "Cash", "status": "Confirmed", "is_paid": "on", "notes": "",
        })
        self.assertRedirects(response, reverse("booking-list"))
        self.assertTrue(Customer.objects.filter(owner=self.user, name="Weekend Warriors", phone="").exists())

    def test_booking_suggests_and_reuses_customer_name_case_insensitively(self):
        existing = Customer.objects.get(owner=self.user, name="Test Customer")
        response = self.client.get(reverse("booking-add"))
        self.assertContains(response, 'id="customerCombobox"')
        self.assertContains(response, 'id="customerSuggestions"')
        self.assertContains(response, '"name": "Test Customer"')
        ground = Ground.objects.get(owner=self.user)

        response = self.client.post(reverse("booking-add"), {
            "customer_name": "test customer", "customer_phone": "",
            "booking_date": date.today(), "booking_time": "13:00", "duration": "1",
            "sport": "Football", "ground": ground.pk, "amount": "500",
            "payment_method": "Cash", "status": "Confirmed", "is_paid": "on", "notes": "",
        })

        self.assertRedirects(response, reverse("booking-list"))
        self.assertEqual(Customer.objects.filter(owner=self.user).count(), 1)
        self.assertEqual(Booking.objects.filter(customer=existing).count(), 2)

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

    def test_daily_analytics_uses_booking_intervals(self):
        ground = Ground.objects.get(owner=self.user)
        turf = ground.turf
        turf.opening_time, turf.closing_time = time(8), time(20)
        turf.save(update_fields=("opening_time", "closing_time"))
        booking = Booking.objects.get(owner=self.user)
        booking.booking_time, booking.duration = time(10), 2
        booking.save(update_fields=("booking_time", "duration"))
        result = get_daily_booking_analytics(date.today(), ground, now=timezone.make_aware(datetime.combine(date.today(), time(7))))
        self.assertEqual(len(result["slots"]), 12)
        self.assertEqual(result["booked_hours"], 2)
        self.assertEqual([s["status"] for s in result["slots"]][2:5], ["BOOKED", "BOOKED", "AVAILABLE"])

    def test_24_hour_and_overnight_operating_hours(self):
        ground = Ground.objects.get(owner=self.user)
        ground.use_custom_hours, ground.is_24_hours = True, True
        ground.save()
        self.assertEqual(len(get_daily_booking_analytics(date.today() + timedelta(days=1), ground)["slots"]), 24)
        ground.is_24_hours, ground.opening_time, ground.closing_time = False, time(18), time(6)
        ground.save()
        result = get_daily_booking_analytics(date.today() + timedelta(days=1), ground)
        self.assertEqual(len(result["slots"]), 12)
        self.assertNotEqual(result["slots"][5]["start_time"][:10], result["slots"][6]["start_time"][:10])

    def test_blocked_slots_and_api(self):
        ground = Ground.objects.get(owner=self.user)
        selected = date.today() + timedelta(days=1)
        start = timezone.make_aware(datetime.combine(selected, time(7)))
        BlockedSlot.objects.create(owner=self.user, ground=ground, start_at=start, end_at=start + timedelta(hours=1))
        result = get_daily_booking_analytics(selected, ground)
        self.assertEqual(next(s for s in result["slots"] if s["start_label"] == "07:00 AM")["status"], "BLOCKED")
        response = self.client.get(reverse("daily-booking-analytics-api", args=[ground.pk]), {"date": selected.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertIn("slots", response.json())
