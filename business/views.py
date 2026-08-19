from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView
from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction
from .forms import BusinessSettingsForm, TurfOnboardingForm
from .models import BusinessSettings, Ground
class SettingsView(LoginRequiredMixin, UpdateView):
    form_class = BusinessSettingsForm
    template_name = "business/settings.html"
    success_url = reverse_lazy("settings")
    def get_object(self): return BusinessSettings.objects.get_or_create(owner=self.request.user)[0]
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["grounds"] = self.object.grounds.all()
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        desired = form.cleaned_data["number_of_grounds"]
        existing = {g.number: g for g in self.object.grounds.all()}
        for number in range(1, desired + 1):
            ground = existing.get(number)
            if ground:
                ground.is_active = True
            else:
                ground = Ground(owner=self.request.user, turf=self.object, number=number)
            ground.name = self.request.POST.get(f"ground_name_{number}", "").strip()
            ground.use_custom_hours = self.request.POST.get(f"ground_custom_hours_{number}") == "on"
            ground.is_24_hours = self.request.POST.get(f"ground_24_hours_{number}") == "on"
            from datetime import datetime
            for field in ("opening_time", "closing_time"):
                raw = self.request.POST.get(f"ground_{field}_{number}", "")
                setattr(ground, field, datetime.strptime(raw, "%H:%M").time() if raw else None)
            ground.save()
        for number, ground in existing.items():
            if number > desired:
                ground.is_active = False
                ground.save(update_fields=("is_active",))
        messages.success(self.request, "Turf profile and grounds updated successfully.")
        return response


class TurfOnboardingView(LoginRequiredMixin, FormView):
    form_class = TurfOnboardingForm
    template_name = "business/onboarding.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        settings = BusinessSettings.objects.get_or_create(owner=request.user)[0]
        if settings.onboarding_completed:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        settings = BusinessSettings.objects.select_for_update().get(owner=self.request.user)
        names = form.cleaned_data["turf_names"]
        settings.number_of_grounds = len(names)
        settings.business_name = names[0]
        settings.onboarding_completed = True
        settings.save(update_fields=("number_of_grounds", "business_name", "onboarding_completed"))
        for number, name in enumerate(names, 1):
            Ground.objects.update_or_create(
                turf=settings, number=number,
                defaults={"owner": self.request.user, "name": name, "is_active": True},
            )
        settings.grounds.filter(number__gt=len(names)).update(is_active=False)
        messages.success(self.request, "Your turf details were saved to your profile.")
        return super().form_valid(form)
