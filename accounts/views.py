from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView

from .forms import EmailOrUsernameAuthenticationForm
from business.views import SettingsView
from django.urls import reverse_lazy


class SignInPageView(LoginView):
    template_name = "account/login.html"
    authentication_form = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True


class ProfileView(SettingsView):
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")
