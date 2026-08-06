from .models import GoogleUserProfile


def _google_data(account):
    data = account.extra_data or {}
    # Recent allauth versions may nest claims under userinfo or id_token.
    claims = data.get("userinfo") or data.get("id_token") or data
    return claims if isinstance(claims, dict) else data


def sync_google_profile(user, account):
    if not user.pk or account.provider != "google":
        return None
    data = _google_data(account)
    full_name = data.get("name", "").strip()
    first_name = data.get("given_name", "").strip()
    last_name = data.get("family_name", "").strip()
    if full_name and not (first_name or last_name):
        first_name, _, last_name = full_name.partition(" ")
    changed = []
    for field, value in (("first_name", first_name), ("last_name", last_name), ("email", data.get("email", "").strip())):
        if value and getattr(user, field) != value:
            setattr(user, field, value)
            changed.append(field)
    if user.has_usable_password():
        user.set_unusable_password()
        changed.append("password")
    if changed:
        user.save(update_fields=changed)
    profile, _ = GoogleUserProfile.objects.get_or_create(user=user)
    profile.google_id = account.uid
    profile.profile_picture = data.get("picture", "")
    profile.role = GoogleUserProfile.Role.OWNER
    profile.status = GoogleUserProfile.Status.ACTIVE
    profile.save()
    return profile
