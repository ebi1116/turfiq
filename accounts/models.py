from django.conf import settings
from django.db import models


class GoogleUserProfile(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_profile",
    )
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_picture = models.URLField(max_length=1000, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Google user"
        verbose_name_plural = "Google users"

    def __str__(self):
        return self.user.get_full_name() or self.user.email or str(self.user)
