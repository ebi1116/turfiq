from django.conf import settings


def is_test_account(user):
    """Return True only for the explicitly configured non-production test user."""
    configured_email = settings.TEST_ACCOUNT_EMAIL.strip().casefold()
    return bool(
        configured_email
        and user.is_authenticated
        and user.email.strip().casefold() == configured_email
    )
