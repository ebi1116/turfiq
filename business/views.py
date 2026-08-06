from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from .forms import BusinessSettingsForm
from .models import BusinessSettings
class SettingsView(LoginRequiredMixin, UpdateView):
    form_class = BusinessSettingsForm
    template_name = "business/settings.html"
    success_url = reverse_lazy("settings")
    def get_object(self): return BusinessSettings.objects.get_or_create(owner=self.request.user)[0]
