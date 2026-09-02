from django import forms
from .models import PlayerProfile, PlayerPost


class PlayerProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, help_text="Shown on your sports profile")
    class Meta:
        model = PlayerProfile
        fields = ("full_name", "photo", "mobile_number", "location", "sport", "position", "skill_level", "date_of_birth", "bio", "favourite_team")
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"}), "bio": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None); super().__init__(*args, **kwargs)
        if user and not self.initial.get("full_name"): self.initial["full_name"] = user.get_full_name()

    def save(self, user, commit=True):
        profile = super().save(commit=False)
        name = self.cleaned_data["full_name"].strip().split(None, 1)
        user.first_name = name[0]; user.last_name = name[1] if len(name) > 1 else ""
        user.save(update_fields=["first_name", "last_name"])
        profile.user = user
        if commit: profile.save()
        return profile


class PlayerPostForm(forms.ModelForm):
    class Meta:
        model = PlayerPost
        fields = ("image", "video", "caption", "sport", "tournament", "turf_tag")
        widgets = {"caption": forms.Textarea(attrs={"rows": 3, "placeholder": "Share a match moment…"})}
