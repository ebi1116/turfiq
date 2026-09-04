from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.views.decorators.cache import never_cache
from django.shortcuts import render

from .forms import ContactForm
from accounts.models import GoogleUserProfile
from accounts.player_analytics import player_analytics


class MarketingPageView(TemplateView):
    pass


class HomeView(TemplateView):
    """Public homepage with a private, data-backed player preview when available."""

    template_name = "marketing/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.request.user, "google_profile", None)
        is_player = bool(
            self.request.user.is_authenticated
            and profile
            and profile.role == GoogleUserProfile.Role.PLAYER
        )
        context["is_player"] = is_player
        context["player_home_analytics"] = player_analytics(self.request.user, "all") if is_player else None
        return context


class ContactView(CreateView):
    form_class = ContactForm
    template_name = "marketing/contact.html"
    success_url = reverse_lazy("contact-thank-you")

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


@never_cache
def service_worker(request):
    response = render(request, "marketing/service_worker.js", content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


def webmanifest(request):
    return JsonResponse({
        "id": "/", "name": "TurfIQ Analytics", "short_name": "TurfIQ",
        "description": "Turf booking, customer and business analytics for turf owners.",
        "start_url": "/dashboard/", "scope": "/", "display": "standalone",
        "display_override": ["window-controls-overlay", "standalone", "minimal-ui"],
        "orientation": "any", "background_color": "#f4f7f5", "theme_color": "#10231c",
        "categories": ["business", "productivity", "sports"],
        "icons": [
            {"src": "/static/images/turfiq-profile-logo-v2.png", "sizes": "1254x1254", "type": "image/png", "purpose": "any"},
            {"src": "/static/images/turfiq-premium-logo.png", "sizes": "1254x1254", "type": "image/png", "purpose": "maskable"},
        ],
        "shortcuts": [
            {"name": "New booking", "short_name": "Book", "url": "/bookings/add/"},
            {"name": "Dashboard", "short_name": "Dashboard", "url": "/dashboard/"},
            {"name": "Customers", "short_name": "Customers", "url": "/bookings/customers/"},
        ],
    }, content_type="application/manifest+json")
