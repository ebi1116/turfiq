from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from .models import Expense
from .forms import ExpenseForm
class OwnedMixin(LoginRequiredMixin):
    def get_queryset(self): return super().get_queryset().filter(owner=self.request.user)
class ExpenseListView(OwnedMixin, ListView): model=Expense; template_name="expenses/list.html"; paginate_by=15
class ExpenseFormMixin(OwnedMixin):
    model=Expense; form_class=ExpenseForm; template_name="expenses/form.html"; success_url=reverse_lazy("expense-list")
    def form_valid(self, form): form.instance.owner=self.request.user; return super().form_valid(form)
class ExpenseCreateView(ExpenseFormMixin, CreateView): pass
class ExpenseUpdateView(ExpenseFormMixin, UpdateView): pass
class ExpenseDeleteView(OwnedMixin, DeleteView): model=Expense; template_name="shared/confirm_delete.html"; success_url=reverse_lazy("expense-list")
