from django.shortcuts import redirect
from django.urls import reverse


class PremiumAccessMiddleware:
    """Let owners explore TurfIQ, but require Premium for data changes."""

    ALLOWED_PREFIXES = ("/admin/", "/billing/", "/accounts/", "/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not user.is_superuser:
            is_allowed = request.path.startswith(self.ALLOWED_PREFIXES)
            if request.path == reverse("logout"):
                is_allowed = True
            from .models import Subscription
            subscription, _ = Subscription.objects.get_or_create(owner=user)
            requires_premium = request.method not in ("GET", "HEAD", "OPTIONS")
            if requires_premium and not is_allowed and not (subscription and subscription.has_access):
                request.session["premium_return_to"] = request.META.get("HTTP_REFERER") or request.path
                return redirect("billing")
        return self.get_response(request)
