from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView

from .forms import EmailOrUsernameAuthenticationForm
from business.views import SettingsView
from django.urls import reverse_lazy
from .adapters import role_login_redirect_url


class SignInPageView(LoginView):
    template_name = "account/login.html"
    authentication_form = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        # Authentication is stored by Django in this request's session.  Role
        # flags select a destination; they never participate in authentication.
        return role_login_redirect_url(self.request.user)



class ProfileView(SettingsView):
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")
