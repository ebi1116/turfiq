from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from allauth.account.views import LogoutView
from accounts.views import ProfileView, SignInPageView
from subscriptions.views import create_order, verify_payment
from marketing.views import service_worker, webmanifest

urlpatterns = [
    path("service-worker.js", service_worker, name="service-worker"),
    path("manifest.webmanifest", webmanifest, name="webmanifest"),
    path("api/create-order", create_order, name="create-order"),
    path("api/verify-payment", verify_payment, name="verify-payment"),
    path("admin/", admin.site.urls),
    path("accounts/login/", SignInPageView.as_view(), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/", include("allauth.urls")),
    path("", include("accounts.urls")),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("billing/", include("subscriptions.urls")),
    path("bookings/", include("bookings.urls")),
    path("expenses/", include("expenses.urls")),
    path("reports/", include("reports.urls")),
    path("tournaments/", include("tournaments.urls")),
    path("settings/", include("business.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("", include("marketing.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
