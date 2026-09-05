from django.contrib import admin

from .models import GoogleUserProfile


@admin.register(GoogleUserProfile)
class GoogleUserProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "google_id", "status", "joined", "last_login")
    list_filter = ("status", "user__is_active")
    search_fields = ("user__first_name", "user__last_name", "user__email", "google_id")
    readonly_fields = ("google_id", "profile_picture", "updated_at")
    list_select_related = ("user",)

    @admin.display(description="Name", ordering="user__first_name")
    def full_name(self, obj):
        return obj.user.get_full_name() or "—"

    @admin.display(ordering="user__email")
    def email(self, obj):
        return obj.user.email

    @admin.display(ordering="user__date_joined")
    def joined(self, obj):
        return obj.user.date_joined

    @admin.display(ordering="user__last_login")
    def last_login(self, obj):
        return obj.user.last_login

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        should_be_active = obj.status == GoogleUserProfile.Status.ACTIVE
        if obj.user.is_active != should_be_active:
            obj.user.is_active = should_be_active
            obj.user.save(update_fields=["is_active"])
