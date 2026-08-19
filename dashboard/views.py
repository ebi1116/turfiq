from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from bookings.models import Booking, Customer
from expenses.models import Expense
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from business.models import BusinessSettings, Ground
from .services import build_dashboard, ground_summaries, get_daily_booking_analytics

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name="dashboard/index.html"
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, "google_profile"):
            settings = BusinessSettings.objects.filter(owner=request.user).first()
            if not settings or not settings.onboarding_completed:
                return redirect("turf-onboarding")
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self,**kwargs):
        ctx=super().get_context_data(**kwargs); ctx.update(build_dashboard(self.request.user))
        ctx["pwa_install_after_login"] = self.request.session.pop("show_pwa_install_prompt", False)
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
        try:
            selected_date = datetime.strptime(self.request.GET.get("date", ""), "%Y-%m-%d").date()
        except ValueError:
            selected_date = timezone.localdate()
        ctx["daily"] = get_daily_booking_analytics(selected_date, ground)
        ctx["selected_date"] = selected_date
        ctx["yesterday"] = timezone.localdate() - timedelta(days=1)
        ctx["today"] = timezone.localdate()
        ctx["tomorrow"] = timezone.localdate() + timedelta(days=1)
        return ctx


@login_required
def daily_booking_analytics_api(request, pk):
    ground = get_object_or_404(Ground, pk=pk, owner=request.user)
    try:
        selected_date = datetime.strptime(request.GET.get("date", ""), "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "date must use YYYY-MM-DD format"}, status=400)
    return JsonResponse(get_daily_booking_analytics(selected_date, ground))
from django.db import models
