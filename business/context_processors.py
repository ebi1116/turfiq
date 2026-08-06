from .models import BusinessSettings
def business_settings(request):
    if request.user.is_authenticated:
        obj, _ = BusinessSettings.objects.get_or_create(owner=request.user)
        return {"business": obj, "currency": obj.currency}
    return {"business": None, "currency": "₹"}
