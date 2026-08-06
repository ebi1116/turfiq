from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import ContactForm


class MarketingPageView(TemplateView):
    pass


class ContactView(CreateView):
    form_class = ContactForm
    template_name = "marketing/contact.html"
    success_url = reverse_lazy("contact")

    def form_valid(self, form):
        messages.success(self.request, "Thanks for contacting TurfIQ. Our team will respond shortly.")
        return super().form_valid(form)


def robots_txt(request):
    body = f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /app/\nSitemap: {request.build_absolute_uri('/sitemap.xml')}\n"
    return HttpResponse(body, content_type="text/plain")


def sitemap_xml(request):
    paths = ("", "about/", "contact/", "faq/", "privacy/", "terms/", "refund-policy/", "shipping-policy/")
    urls = "".join(f"<url><loc>{request.build_absolute_uri('/' + path)}</loc><changefreq>monthly</changefreq></url>" for path in paths)
    return HttpResponse(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', content_type="application/xml")
