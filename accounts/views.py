from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView

from .forms import EmailOrUsernameAuthenticationForm


class SignInPageView(LoginView):
    template_name = "account/login.html"
    authentication_form = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
