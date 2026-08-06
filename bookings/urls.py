from django.urls import path
from .views import *
urlpatterns = [
    path("", BookingListView.as_view(), name="booking-list"), path("add/", BookingCreateView.as_view(), name="booking-add"),
    path("<int:pk>/edit/", BookingUpdateView.as_view(), name="booking-edit"), path("<int:pk>/delete/", BookingDeleteView.as_view(), name="booking-delete"),
    path("customers/", CustomerListView.as_view(), name="customer-list"),
    path("customers/add/", CustomerCreateView.as_view(), name="customer-add"),
]
