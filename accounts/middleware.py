from django.contrib.auth import logout
from django.shortcuts import redirect

from .models import GoogleUserProfile


class ActiveGoogleUserMiddleware:
    """Reject every request from an owner disabled in the TurfIQ admin."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = getattr(request.user, "google_profile", None)
            if profile and profile.status == GoogleUserProfile.Status.DISABLED:
                logout(request)
                return redirect("home")
            # Keep the owner workspace inaccessible to player accounts even
            # when a saved/bookmarked owner URL is opened directly.
            owner_prefixes = ("/dashboard/", "/bookings/", "/expenses/", "/reports/", "/settings/")
            if profile and profile.role == GoogleUserProfile.Role.PLAYER and request.path.startswith(owner_prefixes):
                return redirect("player-dashboard")
        return self.get_response(request)
