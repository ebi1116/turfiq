from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from allauth.core.exceptions import ImmediateHttpResponse
import logging

from .services import sync_google_profile

logger = logging.getLogger(__name__)


def role_login_redirect_url(user):
    """Return the landing page for this authenticated user only."""
    if user.is_superuser or user.is_staff:
        return reverse("admin:index")
    if not hasattr(user, "google_profile") or not user.google_profile.role:
        return reverse("choose-role")
    if user.google_profile.role == "player":
        return reverse("player-onboarding") if not hasattr(user, "player_profile") else reverse("player-dashboard")
    from business.models import BusinessSettings
    settings = BusinessSettings.objects.filter(owner=user).first()
    if hasattr(user, "google_profile") and (not settings or not settings.onboarding_completed):
        return reverse("turf-onboarding")
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

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        logger.warning(
            "Google authentication callback failed (authenticated=%s, error=%s, exception=%s)",
            request.user.is_authenticated,
            error or "unknown",
            exception.__class__.__name__ if exception else "none",
        )
        if request.user.is_authenticated:
            messages.info(request, "You are already signed in.")
            raise ImmediateHttpResponse(redirect(role_login_redirect_url(request.user)))
        messages.error(request, "Google sign-in could not be completed. Please try again.")
        raise ImmediateHttpResponse(redirect("login"))

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=None)
        user.set_unusable_password()
        user.is_active = True
        user.save(update_fields=["password", "is_active"])
        sync_google_profile(user, sociallogin.account)
        return user
