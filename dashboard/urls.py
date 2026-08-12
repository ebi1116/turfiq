from django.urls import path
from .views import DashboardView, GroundAnalyticsView
urlpatterns=[path("",DashboardView.as_view(),name="dashboard"), path("grounds/<int:pk>/", GroundAnalyticsView.as_view(), name="ground-analytics")]
