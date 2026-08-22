from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import GoogleUserProfile
from .services import sync_google_profile
from .adapters import GoogleOnlySocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory


class AuthenticationTests(TestCase):
    def test_login_page_only_has_google_authentication(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Continue with Google")
        self.assertContains(response, 'action="/accounts/google/login/"')
        self.assertNotContains(response, 'type="password"')
        self.assertNotContains(response, 'name="username"')
        self.assertEqual(self.client.post(reverse("login"), {}).status_code, 405)

    def test_authenticated_owner_skips_entry_page(self):
        user = User.objects.create_user(username="existing-owner")
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("login")), "/dashboard/")
        self.assertEqual(reverse("dashboard"), "/dashboard/")

    def test_superuser_and_owner_sessions_are_independent(self):
        admin = User.objects.create_superuser("admin", "admin@example.com", "AdminPass123!")
        owner = User.objects.create_user("owner-two", "owner@example.com", "OwnerPass123!")
        admin_client = Client()
        owner_client = Client()

        admin_client.force_login(admin)
        owner_client.force_login(owner)

        self.assertRedirects(admin_client.get(reverse("login")), reverse("admin:index"))
        self.assertRedirects(owner_client.get(reverse("login")), reverse("dashboard"))
        self.assertEqual(int(admin_client.session["_auth_user_id"]), admin.pk)
        self.assertEqual(int(owner_client.session["_auth_user_id"]), owner.pk)
        self.assertNotEqual(admin_client.session.session_key, owner_client.session.session_key)

        admin_client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", admin_client.session)
        self.assertEqual(int(owner_client.session["_auth_user_id"]), owner.pk)

        admin_client.force_login(admin)
        owner_client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", owner_client.session)
        self.assertEqual(int(admin_client.session["_auth_user_id"]), admin.pk)

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

    def test_new_google_owner_completes_turf_setup_before_dashboard(self):
        user = User.objects.create_user(username="new-google-owner")
        GoogleUserProfile.objects.create(user=user)
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("dashboard")), reverse("turf-onboarding"))

        response = self.client.post(reverse("turf-onboarding"), {
            "number_of_grounds": 2,
            "turf_name_1": "North Arena",
            "turf_name_2": "South Arena",
        })

        self.assertRedirects(response, reverse("dashboard"))
        settings = user.business_settings
        self.assertTrue(settings.onboarding_completed)
        self.assertEqual(settings.number_of_grounds, 2)
        self.assertEqual(list(settings.grounds.values_list("name", flat=True)), ["North Arena", "South Arena"])

    def test_logout_destroys_session_and_returns_home(self):
        user = User.objects.create_user(username="owner")
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_google_callback_error_recovers_authenticated_mobile_session(self):
        user = User.objects.create_user(username="mobile-owner")
        request = RequestFactory().get("/accounts/google/login/callback/")
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request.user = user
        setattr(request, "_messages", FallbackStorage(request))

        with self.assertRaises(ImmediateHttpResponse) as captured:
            GoogleOnlySocialAccountAdapter().on_authentication_error(
                request, provider=type("Provider", (), {"id": "google"})(), error="oauth_error"
            )

        self.assertEqual(captured.exception.response.url, reverse("dashboard"))

    def test_google_callback_error_returns_anonymous_mobile_user_to_login(self):
        from django.contrib.auth.models import AnonymousUser
        request = RequestFactory().get("/accounts/google/login/callback/")
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request.user = AnonymousUser()
        setattr(request, "_messages", FallbackStorage(request))

        with self.assertRaises(ImmediateHttpResponse) as captured:
            GoogleOnlySocialAccountAdapter().on_authentication_error(
                request, provider=type("Provider", (), {"id": "google"})(), error="oauth_error"
            )

        self.assertEqual(captured.exception.response.url, reverse("login"))
