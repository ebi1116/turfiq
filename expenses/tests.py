from datetime import date

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from .admin import ExpenseAdmin
from .models import Expense
from django.urls import reverse
from subscriptions.models import Subscription


class ExpenseAdminIsolationTests(TestCase):
    def setUp(self):
        self.owner_a = User.objects.create_user("expense-owner-a", is_staff=True)
        self.owner_b = User.objects.create_user("expense-owner-b", is_staff=True)
        self.superuser = User.objects.create_superuser("expense-root", "root@example.com", "password")
        self.expense_a = Expense.objects.create(owner=self.owner_a, category="Rent", amount=1000, expense_date=date.today())
        self.expense_b = Expense.objects.create(owner=self.owner_b, category="Water", amount=500, expense_date=date.today())
        self.model_admin = ExpenseAdmin(Expense, admin.site)
        self.factory = RequestFactory()

    def request_for(self, user):
        request = self.factory.get("/admin/expenses/expense/")
        request.user = user
        return request

    def test_owner_only_sees_own_expenses(self):
        self.assertEqual(list(self.model_admin.get_queryset(self.request_for(self.owner_a))), [self.expense_a])

    def test_superuser_sees_all_expenses(self):
        queryset = self.model_admin.get_queryset(self.request_for(self.superuser))
        self.assertEqual(set(queryset), {self.expense_a, self.expense_b})

    def test_owner_cannot_open_another_owners_expense(self):
        self.assertFalse(self.model_admin.has_view_permission(self.request_for(self.owner_a), self.expense_b))


class ExpenseManualEntryTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("expense-form-owner", password="test-pass-123")
        Subscription.objects.create(owner=self.owner, status="active")
        self.client.force_login(self.owner)

    def test_category_and_amount_are_manual_text_inputs(self):
        response = self.client.get(reverse("expense-add"))
        self.assertContains(response, 'list="expense-category-options"')
        self.assertNotContains(response, 'name="amount" type="number"')
        response = self.client.post(reverse("expense-add"), {
            "category": "Marketing", "amount": "1250.75",
            "expense_date": date.today(), "notes": "Campaign",
        })
        self.assertRedirects(response, reverse("expense-list"))
        self.assertTrue(Expense.objects.filter(owner=self.owner, category="Marketing").exists())
