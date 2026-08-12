from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
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
        response = super().form_valid(form)
        enquiry = self.object
        email = EmailMessage(
            subject=f"TurfIQ enquiry: {enquiry.subject}",
            body=(
                f"Name: {enquiry.name}\n"
                f"Email: {enquiry.email}\n"
                f"Phone: {enquiry.phone or 'Not provided'}\n\n"
                f"Message:\n{enquiry.message}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.SUPPORT_EMAIL],
            reply_to=[enquiry.email],
        )
        try:
            email.send(fail_silently=False)
        except Exception:
            messages.warning(
                self.request,
                "Your message was saved, but email delivery is temporarily unavailable. You can email support@turfiq.in directly.",
            )
            return response
        messages.success(self.request, "Thanks for contacting TurfIQ. Our team will respond shortly.")
        return response


def robots_txt(request):
    body = f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /app/\nSitemap: {request.build_absolute_uri('/sitemap.xml')}\n"
    return HttpResponse(body, content_type="text/plain")


def sitemap_xml(request):
    paths = ("", "about/", "contact/", "faq/", "privacy/", "terms/", "refund-policy/", "shipping-policy/")
    urls = "".join(f"<url><loc>{request.build_absolute_uri('/' + path)}</loc><changefreq>monthly</changefreq></url>" for path in paths)
    return HttpResponse(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', content_type="application/xml")
