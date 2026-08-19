from django.urls import path
from .views import SettingsView, TurfOnboardingView
urlpatterns = [path("", SettingsView.as_view(), name="settings"), path("onboarding/", TurfOnboardingView.as_view(), name="turf-onboarding")]
