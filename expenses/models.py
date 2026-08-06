from django.contrib.auth.models import User
from django.db import models
class Expense(models.Model):
    CATEGORIES = [(x, x) for x in ("Electricity", "Salary", "Maintenance", "Water", "Internet", "Rent", "Cleaning", "Other")]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=30, choices=CATEGORIES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField(db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-expense_date", "-created_at"]
    def __str__(self): return f"{self.category} — {self.amount}"
