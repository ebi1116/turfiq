from django import forms
from .models import Expense
class ExpenseForm(forms.ModelForm):
    category = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"list": "expense-category-options", "autocomplete": "off", "placeholder": "Type or select a category"}),
    )

    class Meta:
        model = Expense; exclude = ("owner",)
        widgets = {
            "amount": forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off", "placeholder": "Enter amount"}),
            "expense_date": forms.DateInput(attrs={"type":"date"}),
            "notes": forms.Textarea(attrs={"rows":3}),
        }

    def clean_category(self):
        return self.cleaned_data["category"].strip()
