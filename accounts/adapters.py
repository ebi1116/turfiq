from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .services import sync_google_profile


class GoogleOnlySocialAccountAdapter(DefaultSocialAccountAdapter):
    """Auto-provision Google owners without exposing an intermediate signup form."""

    def is_open_for_signup(self, request, sociallogin):
        return sociallogin.account.provider == "google"

    def is_auto_signup_allowed(self, request, sociallogin):
        return sociallogin.account.provider == "google"

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=None)
        user.set_unusable_password()
        user.is_active = True
        user.save(update_fields=["password", "is_active"])
        sync_google_profile(user, sociallogin.account)
        return user
