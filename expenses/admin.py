from django.contrib import admin

from turfiq.admin_mixins import OwnerScopedAdminMixin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(OwnerScopedAdminMixin, admin.ModelAdmin):
    list_display = ("category", "amount", "expense_date", "turf_owner", "short_notes")
    list_filter = ("owner", "category", "expense_date")
    search_fields = ("category", "notes", "owner__username", "owner__first_name")
    date_hierarchy = "expense_date"
    ordering = ("-expense_date", "owner__username")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner")

    def get_list_display(self, request):
        if request.user.is_superuser:
            return self.list_display
        return ("category", "amount", "expense_date", "short_notes")

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return self.list_filter
        return ("category", "expense_date")

    @admin.display(description="Turf owner", ordering="owner__username")
    def turf_owner(self, obj):
        return obj.owner.get_full_name() or obj.owner.username

    @admin.display(description="Notes")
    def short_notes(self, obj):
        return obj.notes[:60] if obj.notes else "—"
