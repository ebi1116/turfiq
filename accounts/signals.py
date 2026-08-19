from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .services import sync_google_profile


@receiver(social_account_added)
@receiver(social_account_updated)
def sync_changed_google_account(request, sociallogin, **kwargs):
    sync_google_profile(sociallogin.user, sociallogin.account)


@receiver(user_logged_in)
def sync_google_user_on_login(sender, request, user, **kwargs):
    account = user.socialaccount_set.filter(provider="google").first()
    if account:
        sync_google_profile(user, account)
