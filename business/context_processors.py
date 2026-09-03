from .models import BusinessSettings
def business_settings(request):
    if request.user.is_authenticated:
        role = getattr(getattr(request.user, "google_profile", None), "role", None)
        if role != "owner":
            return {"business": None, "currency": "₹"}
        obj, _ = BusinessSettings.objects.get_or_create(owner=request.user)
        return {"business": obj, "currency": obj.currency}
    return {"business": None, "currency": "₹"}
