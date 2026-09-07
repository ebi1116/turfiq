from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import models, transaction
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from business.models import Ground
from dashboard.services import get_daily_booking_analytics
from .forms import BookingForm, CustomerForm
from .models import Booking, Customer

class OwnedMixin(LoginRequiredMixin):
    def get_queryset(self): return super().get_queryset().filter(owner=self.request.user)

class BookingListView(OwnedMixin, ListView):
    model = Booking; template_name = "bookings/list.html"; paginate_by = 15

    @staticmethod
    def _date(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    def get_queryset(self):
        qs = super().get_queryset().select_related("customer")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(customer__name__icontains=q)
        customer = self.request.GET.get("customer")
        ground = self.request.GET.get("ground")
        if customer:
            qs = qs.filter(customer_id=customer)
        if ground:
            qs = qs.filter(ground_id=ground)
        payment_status = self.request.GET.get("payment_status")
        if payment_status == "paid":
            qs = qs.filter(is_paid=True)
        elif payment_status == "pending":
            qs = qs.filter(is_paid=False)
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        self.selected_date = self._date(self.request.GET.get("date")) or timezone.localdate()
        self.date_range = self.request.GET.get("range")
        if self.date_range == "yesterday":
            start = end = timezone.localdate() - timedelta(days=1)
        elif self.date_range == "this_week":
            start, end = timezone.localdate() - timedelta(days=timezone.localdate().weekday()), timezone.localdate()
        elif self.date_range == "this_month":
            start, end = timezone.localdate().replace(day=1), timezone.localdate()
        elif self.date_range == "custom":
            start = self._date(self.request.GET.get("from_date"))
            end = self._date(self.request.GET.get("to_date"))
            if not start or not end or end < start:
                start = end = self.selected_date
        else:
            start = end = self.selected_date
        self.start_date, self.end_date = start, end
        return qs.filter(booking_date__range=(start, end))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtered = self.get_queryset()
        active = filtered.exclude(status="Cancelled")
        totals = active.aggregate(revenue=Sum("amount"), paid=Sum("amount", filter=models.Q(is_paid=True)), pending=Sum("amount", filter=models.Q(is_paid=False)))
        context.update({
            "selected_date": self.selected_date, "start_date": self.start_date, "end_date": self.end_date,
            "previous_date": self.selected_date - timedelta(days=1), "next_date": self.selected_date + timedelta(days=1),
            "is_range": self.start_date != self.end_date, "summary": {
                "total": filtered.count(), "revenue": totals["revenue"] or 0,
                "paid": totals["paid"] or 0, "pending": totals["pending"] or 0,
                "cancelled": filtered.filter(status="Cancelled").count(),
            },
            "customers": Customer.objects.filter(owner=self.request.user).order_by("name"),
            "grounds": Ground.objects.filter(owner=self.request.user, is_active=True).order_by("number"),
            "slot_view": self.request.GET.get("view") == "slot",
        })
        if context["slot_view"]:
            context["slot_days"] = [
                {"ground": ground, "daily": get_daily_booking_analytics(self.selected_date, ground)}
                for ground in context["grounds"]
            ]
        return context

class BookingFormMixin(OwnedMixin):
    model = Booking; form_class = BookingForm; template_name = "bookings/form.html"; success_url = reverse_lazy("booking-list")
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer_options"] = list(Customer.objects.filter(owner=self.request.user).order_by("name").values("name", "phone"))
        return context
    def form_valid(self, form):
        with transaction.atomic():
            name = form.cleaned_data["customer_name"]
            phone = form.cleaned_data["customer_phone"]
            customer = Customer.objects.filter(owner=self.request.user, name__iexact=name).first()
            if customer is None and phone:
                customer = Customer.objects.filter(owner=self.request.user, phone=phone).first()
            if customer is None and form.instance.pk and not phone and not form.instance.customer.phone:
                customer = form.instance.customer
            if customer is None:
                customer = Customer.objects.create(owner=self.request.user, name=name, phone=phone)
            else:
                changed = []
                phone_available = not Customer.objects.filter(owner=self.request.user, phone=phone).exclude(pk=customer.pk).exists() if phone else False
                if phone and not customer.phone and phone_available:
                    customer.phone = phone
                    changed.append("phone")
                if changed:
                    customer.save(update_fields=changed)
            form.instance.customer = customer
            form.instance.owner = self.request.user
            messages.success(self.request, "Booking saved. Customer or team was added to Customers automatically.")
            return super().form_valid(form)
class BookingCreateView(BookingFormMixin, CreateView): pass
class BookingUpdateView(BookingFormMixin, UpdateView): pass
class BookingDeleteView(OwnedMixin, DeleteView):
    model = Booking; template_name = "shared/confirm_delete.html"; success_url = reverse_lazy("booking-list")

class BookingDetailView(OwnedMixin, DetailView):
    model = Booking
    template_name = "bookings/detail.html"

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer; template_name = "bookings/customers.html"; paginate_by = 15
    def get_queryset(self): return Customer.objects.filter(owner=self.request.user).annotate(total_bookings=models.Count("bookings"), total_spend=models.Sum("bookings__amount")).order_by("-total_spend")


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "bookings/customer_form.html"
    success_url = reverse_lazy("customer-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Customer added successfully. You can now select them in a new booking.")
        return super().form_valid(form)
from django.db import models
