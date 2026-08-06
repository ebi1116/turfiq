class OwnerScopedAdminMixin:
    """Restrict tenant-owned admin records to the signed-in turf owner."""

    owner_field = "owner"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(**{self.owner_field: request.user})

    def get_exclude(self, request, obj=None):
        excluded = list(super().get_exclude(request, obj) or ())
        if not request.user.is_superuser and self.owner_field not in excluded:
            excluded.append(self.owner_field)
        return excluded

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            setattr(obj, self.owner_field, request.user)
        super().save_model(request, obj, form, change)

    def _owns_object(self, request, obj):
        return obj is None or request.user.is_superuser or obj.owner_id == request.user.id

    def has_view_permission(self, request, obj=None):
        return super().has_view_permission(request, obj) and self._owns_object(request, obj)

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and self._owns_object(request, obj)

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and self._owns_object(request, obj)
