from django.urls import path
from .views import DashboardView, GroundAnalyticsView, daily_booking_analytics_api
urlpatterns=[path("",DashboardView.as_view(),name="dashboard"), path("grounds/<int:pk>/", GroundAnalyticsView.as_view(), name="ground-analytics"), path("api/grounds/<int:pk>/daily-analytics/", daily_booking_analytics_api, name="daily-booking-analytics-api")]
