from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or username",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "username", "placeholder": "Email or username"}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password", "placeholder": "Password"}),
    )

    def clean(self):
        identifier = self.cleaned_data.get("username", "").strip()
        if "@" in identifier:
            user = get_user_model().objects.filter(email__iexact=identifier).only("username").first()
            if user:
                self.cleaned_data["username"] = user.get_username()
        return super().clean()
