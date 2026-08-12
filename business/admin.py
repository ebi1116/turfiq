from django.contrib import admin
from django.db.models import Count

from bookings.models import Customer
from expenses.models import Expense
from .models import BusinessSettings, Ground, TurfOwnerWorkspace

admin.site.register(Ground)


@admin.register(BusinessSettings)
class BusinessSettingsAdmin(admin.ModelAdmin):
    list_display = ("business_name", "owner", "currency", "opening_time", "closing_time")
    search_fields = ("business_name", "owner__username", "owner__first_name", "owner__last_name")
    list_filter = ("currency", "timezone")


@admin.register(TurfOwnerWorkspace)
class TurfOwnerWorkspaceAdmin(admin.ModelAdmin):
    """A folder-like admin directory with tenant data shown inside each owner."""

    change_form_template = "admin/business/turf_owner_workspace/change_form.html"
    list_display = ("folder_name", "owner_username", "customer_total", "expense_total")
    search_fields = ("username", "first_name", "last_name", "business_settings__business_name")
    ordering = ("pk",)
    readonly_fields = ("id", "username", "first_name", "last_name", "email", "turf_name")
    fields = ("id", "turf_name", "username", "first_name", "last_name", "email")

    class Media:
        css = {"all": ("admin/css/workspace-folders.css",)}

    def get_queryset(self, request):
        queryset = super().get_queryset(request).filter(business_settings__isnull=False).select_related("business_settings").annotate(
            workspace_customer_count=Count("customers", distinct=True),
            workspace_expense_count=Count("expenses", distinct=True),
        )
        if request.user.is_superuser:
            return queryset
        return queryset.filter(pk=request.user.pk)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        allowed = super().has_change_permission(request, obj)
        return allowed and (obj is None or request.user.is_superuser or obj.pk == request.user.pk)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        owner = self.get_object(request, object_id)
        extra_context = extra_context or {}
        if owner:
            extra_context.update({
                "workspace_customers": Customer.objects.filter(owner=owner).annotate(booking_total=Count("bookings")).order_by("name"),
                "workspace_expenses": Expense.objects.filter(owner=owner).order_by("-expense_date", "-created_at"),
                "workspace_owner": owner,
                "show_save": False,
                "show_save_and_continue": False,
                "show_save_and_add_another": False,
            })
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.display(description="Owner folder", ordering="pk")
    def folder_name(self, obj):
        return f"📁 {obj.pk} — {obj.business_settings.business_name}"

    @admin.display(description="Account", ordering="username")
    def owner_username(self, obj):
        return obj.get_full_name() or obj.username

    @admin.display(description="Customers", ordering="workspace_customer_count")
    def customer_total(self, obj):
        return obj.workspace_customer_count

    @admin.display(description="Expenses", ordering="workspace_expense_count")
    def expense_total(self, obj):
        return obj.workspace_expense_count

    @admin.display(description="Turf name")
    def turf_name(self, obj):
        return obj.business_settings.business_name
