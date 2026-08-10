from django.shortcuts import redirect
from django.urls import reverse

from .access import is_test_account


class PremiumAccessMiddleware:
    """Require account-specific Premium access for every workspace request."""

    ALLOWED_PREFIXES = ("/admin/", "/billing/", "/accounts/", "/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        request.is_test_account = is_test_account(user)
        if user.is_authenticated and not user.is_superuser and not request.is_test_account:
            is_allowed = request.path.startswith(self.ALLOWED_PREFIXES)
            if request.path == reverse("logout"):
                is_allowed = True
            from .models import Subscription
            subscription, _ = Subscription.objects.get_or_create(owner=user)
            if not is_allowed and not subscription.has_access:
                request.session["premium_return_to"] = request.META.get("HTTP_REFERER") or request.path
                return redirect("billing")
        return self.get_response(request)
