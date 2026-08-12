from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from bookings.models import Booking, Customer
from expenses.models import Expense
from django.shortcuts import get_object_or_404
from business.models import Ground
from .services import build_dashboard, ground_summaries

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name="dashboard/index.html"
    def get_context_data(self,**kwargs):
        ctx=super().get_context_data(**kwargs); ctx.update(build_dashboard(self.request.user))
        ctx["grounds"] = ground_summaries(self.request.user)
        ctx["recent_bookings"]=Booking.objects.filter(owner=self.request.user).select_related("customer")[:6]
        ctx["recent_expenses"]=Expense.objects.filter(owner=self.request.user)[:5]
        ctx["top_customers"]=Customer.objects.filter(owner=self.request.user).annotate(total=models.Sum("bookings__amount"),visits=models.Count("bookings")).order_by("-total")[:5]
        return ctx


class GroundAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/ground_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ground = get_object_or_404(Ground, pk=kwargs["pk"], owner=self.request.user)
        ctx.update(build_dashboard(self.request.user, ground))
        ctx["ground"] = ground
        return ctx
from django.db import models
