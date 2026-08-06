from django.urls import path
from .views import billing, razorpay_webhook, verify_checkout

urlpatterns = [
    path("", billing, name="billing"),
    path("verify/", verify_checkout, name="billing-verify"),
    path("webhook/", razorpay_webhook, name="razorpay-webhook"),
]
