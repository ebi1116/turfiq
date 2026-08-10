from django.shortcuts import redirect
from django.urls import Resolver404, resolve, reverse

from .access import is_test_account


class PremiumAccessMiddleware:
    """Keep onboarding free, then require account-specific Premium features."""

    ALLOWED_PREFIXES = ("/admin/", "/billing/", "/accounts/", "/static/", "/media/")
    FREE_ROUTE_NAMES = {"dashboard", "customer-list", "customer-add", "profile", "logout"}

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
            request.has_premium_access = subscription.has_access
            try:
                is_allowed = is_allowed or resolve(request.path_info).url_name in self.FREE_ROUTE_NAMES
            except Resolver404:
                pass
            if not is_allowed and not subscription.has_access:
                request.session["premium_return_to"] = request.META.get("HTTP_REFERER") or request.path
                return redirect("billing")
        elif user.is_authenticated:
            request.has_premium_access = True
        return self.get_response(request)
