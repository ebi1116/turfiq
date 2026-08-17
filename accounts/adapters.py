from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse

from .services import sync_google_profile


def role_login_redirect_url(user):
    """Return the landing page for this authenticated user only."""
    if user.is_superuser or user.is_staff:
        return reverse("admin:index")
    return reverse("dashboard")


class TurfIQAccountAdapter(DefaultAccountAdapter):
    """Apply the same role-based landing page to allauth/Google logins."""

    def get_login_redirect_url(self, request):
        return role_login_redirect_url(request.user)


class GoogleOnlySocialAccountAdapter(DefaultSocialAccountAdapter):
    """Auto-provision Google owners without exposing an intermediate signup form."""

    def is_open_for_signup(self, request, sociallogin):
        return sociallogin.account.provider == "google"

    def is_auto_signup_allowed(self, request, sociallogin):
        return sociallogin.account.provider == "google"

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=None)
        user.set_unusable_password()
        user.is_active = True
        user.save(update_fields=["password", "is_active"])
        sync_google_profile(user, sociallogin.account)
        return user
