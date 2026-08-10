from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import GoogleUserProfile
from .services import sync_google_profile


class AuthenticationTests(TestCase):
    def test_login_page_has_password_and_google_authentication(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign In")
        self.assertContains(response, "Login with Google")
        self.assertContains(response, 'action="/accounts/google/login/"')
        self.assertContains(response, 'type="password"')
        self.assertContains(response, 'name="username"')

    def test_owner_can_sign_in_with_email_and_password(self):
        user = User.objects.create_user("demo", "demo@turfiq.local", "Demo@12345")

        response = self.client.post(reverse("login"), {"username": user.email, "password": "Demo@12345"})

        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_authenticated_owner_skips_entry_page(self):
        user = User.objects.create_user(username="existing-owner")
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("login")), "/dashboard/")
        self.assertEqual(reverse("dashboard"), "/dashboard/")

    def test_legacy_authentication_routes_are_removed(self):
        for path in (
            "/accounts/register/", "/accounts/signup/", "/accounts/password-reset/",
            "/accounts/password/reset/", "/accounts/password/change/", "/accounts/reset/done/",
        ):
            self.assertEqual(self.client.get(path).status_code, 404, path)

    def test_business_routes_redirect_to_google_entry_page(self):
        for name in ("dashboard", "reports", "customer-list", "booking-list", "expense-list", "settings"):
            target = reverse(name)
            response = self.client.get(target)
            self.assertRedirects(response, f"{reverse('login')}?next={target}")

    def test_google_details_are_stored_and_password_is_unusable(self):
        user = User.objects.create_user(username="google-owner", email="old@example.com", password="temporary")
        account = SocialAccount.objects.create(
            user=user,
            provider="google",
            uid="google-sub-123",
            extra_data={
                "sub": "google-sub-123",
                "name": "Asha Nair",
                "given_name": "Asha",
                "family_name": "Nair",
                "email": "asha@example.com",
                "picture": "https://example.com/asha.jpg",
            },
        )
        profile = sync_google_profile(user, account)
        user.refresh_from_db()
        self.assertEqual(user.get_full_name(), "Asha Nair")
        self.assertEqual(user.email, "asha@example.com")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(profile.google_id, "google-sub-123")
        self.assertEqual(profile.profile_picture, "https://example.com/asha.jpg")
        self.assertEqual(profile.role, GoogleUserProfile.Role.OWNER)
        self.assertEqual(profile.status, GoogleUserProfile.Status.ACTIVE)

    def test_disabled_google_owner_is_logged_out(self):
        user = User.objects.create_user(username="disabled-owner")
        GoogleUserProfile.objects.create(user=user, status=GoogleUserProfile.Status.DISABLED)
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_destroys_session_and_returns_home(self):
        user = User.objects.create_user(username="owner")
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)
