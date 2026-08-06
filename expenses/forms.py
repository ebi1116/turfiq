from django import forms
from .models import Expense
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense; exclude = ("owner",)
        widgets = {"expense_date": forms.DateInput(attrs={"type":"date"}), "notes": forms.Textarea(attrs={"rows":3})}
