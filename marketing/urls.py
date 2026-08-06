from django.urls import path
from .views import ContactView, MarketingPageView, robots_txt, sitemap_xml

urlpatterns = [
    path("", MarketingPageView.as_view(template_name="marketing/home.html"), name="home"),
    path("about/", MarketingPageView.as_view(template_name="marketing/about.html"), name="about"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("faq/", MarketingPageView.as_view(template_name="marketing/faq.html"), name="faq"),
    path("privacy/", MarketingPageView.as_view(template_name="marketing/privacy.html"), name="privacy"),
    path("terms/", MarketingPageView.as_view(template_name="marketing/terms.html"), name="terms"),
    path("refund-policy/", MarketingPageView.as_view(template_name="marketing/refund.html"), name="refund-policy"),
    path("shipping-policy/", MarketingPageView.as_view(template_name="marketing/shipping.html"), name="shipping-policy"),
    path("robots.txt", robots_txt, name="robots-txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap"),
]
