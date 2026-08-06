from django.contrib import admin
from django.db import models
from turfiq.admin_mixins import OwnerScopedAdminMixin

from .models import Booking, Customer


@admin.register(Customer)
class CustomerAdmin(OwnerScopedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "phone", "email", "turf_owner", "booking_count", "created_at")
    search_fields = ("name", "phone", "email", "owner__username", "owner__first_name")
    list_filter = ("owner", "created_at")
    ordering = ("owner__username", "name")
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner").annotate(admin_booking_count=models.Count("bookings"))

    def get_list_display(self, request):
        # The owner column is unnecessary for tenant users because every row is theirs.
        if request.user.is_superuser:
            return self.list_display
        return ("name", "phone", "email", "booking_count", "created_at")

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return self.list_filter
        return ("created_at",)

    @admin.display(description="Turf owner", ordering="owner__username")
    def turf_owner(self, obj):
        return obj.owner.get_full_name() or obj.owner.username

    @admin.display(description="Bookings", ordering="admin_booking_count")
    def booking_count(self, obj):
        return obj.admin_booking_count


@admin.register(Booking)
class BookingAdmin(OwnerScopedAdminMixin, admin.ModelAdmin):
    list_display = ("customer", "booking_date", "booking_time", "sport", "amount", "status")
    list_filter = ("status", "sport", "payment_method")
    search_fields = ("customer__name", "customer__phone", "ground")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "customer" and not request.user.is_superuser:
            kwargs["queryset"] = Customer.objects.filter(owner=request.user).order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
