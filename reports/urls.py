from django.urls import path
from .views import export_report,report_view
urlpatterns=[path("",report_view,name="reports"),path("export/<str:format>/",export_report,name="report-export")]
