from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from business.views import SettingsView
from .adapters import role_login_redirect_url


class SignInPageView(TemplateView):
    template_name = "account/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(role_login_redirect_url(request.user))
        return super().dispatch(request, *args, **kwargs)


class ProfileView(SettingsView):
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")
