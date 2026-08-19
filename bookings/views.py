from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from .forms import BookingForm, CustomerForm
from .models import Booking, Customer

class OwnedMixin(LoginRequiredMixin):
    def get_queryset(self): return super().get_queryset().filter(owner=self.request.user)

class BookingListView(OwnedMixin, ListView):
    model = Booking; template_name = "bookings/list.html"; paginate_by = 15
    def get_queryset(self):
        qs = super().get_queryset().select_related("customer")
        q = self.request.GET.get("q")
        return qs.filter(customer__name__icontains=q) if q else qs

class BookingFormMixin(OwnedMixin):
    model = Booking; form_class = BookingForm; template_name = "bookings/form.html"; success_url = reverse_lazy("booking-list")
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
    def form_valid(self, form):
        with transaction.atomic():
            name = form.cleaned_data["customer_name"]
            phone = form.cleaned_data["customer_phone"]
            customer = Customer.objects.filter(owner=self.request.user, phone=phone).first() if phone else None
            if customer is None and form.instance.pk and not phone and not form.instance.customer.phone:
                customer = form.instance.customer
            if customer is None and not phone:
                customer = Customer.objects.filter(owner=self.request.user, phone="", name__iexact=name).first()
            if customer is None:
                customer = Customer.objects.create(owner=self.request.user, name=name, phone=phone)
            elif customer.name != name:
                customer.name = name
                customer.save(update_fields=("name",))
            form.instance.customer = customer
            form.instance.owner = self.request.user
            messages.success(self.request, "Booking saved. Customer or team was added to Customers automatically.")
            return super().form_valid(form)
class BookingCreateView(BookingFormMixin, CreateView): pass
class BookingUpdateView(BookingFormMixin, UpdateView): pass
class BookingDeleteView(OwnedMixin, DeleteView):
    model = Booking; template_name = "shared/confirm_delete.html"; success_url = reverse_lazy("booking-list")

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer; template_name = "bookings/customers.html"; paginate_by = 15
    def get_queryset(self): return Customer.objects.filter(owner=self.request.user).annotate(total_bookings=models.Count("bookings"), total_spend=models.Sum("bookings__amount")).order_by("-total_spend")


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "bookings/customer_form.html"
    success_url = reverse_lazy("customer-list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Customer added successfully. You can now select them in a new booking.")
        return super().form_valid(form)
from django.db import models
