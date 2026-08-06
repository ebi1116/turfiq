from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from .admin import CustomerAdmin
from .models import Customer


class CustomerAdminIsolationTests(TestCase):
    def setUp(self):
        self.owner_a = User.objects.create_user("owner-a", is_staff=True)
        self.owner_b = User.objects.create_user("owner-b", is_staff=True)
        self.superuser = User.objects.create_superuser("root", "root@example.com", "password")
        self.customer_a = Customer.objects.create(owner=self.owner_a, name="Customer A", phone="100")
        self.customer_b = Customer.objects.create(owner=self.owner_b, name="Customer B", phone="200")
        self.model_admin = CustomerAdmin(Customer, admin.site)
        self.factory = RequestFactory()

    def request_for(self, user):
        request = self.factory.get("/admin/bookings/customer/")
        request.user = user
        return request

    def test_turf_owner_only_sees_own_customers(self):
        queryset = self.model_admin.get_queryset(self.request_for(self.owner_a))
        self.assertEqual(list(queryset), [self.customer_a])

    def test_superuser_can_audit_all_customers(self):
        queryset = self.model_admin.get_queryset(self.request_for(self.superuser))
        self.assertEqual(set(queryset), {self.customer_a, self.customer_b})

    def test_turf_owner_cannot_open_another_owners_customer(self):
        request = self.request_for(self.owner_a)
        self.assertFalse(self.model_admin.has_view_permission(request, self.customer_b))
