from django.contrib import admin
from .models import HealthCheck

@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    list_display = ("forename", "surname", "bmi", "diastolic", "created_by", "created_at")
    list_filter = ("created_at", "created_by")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser or getattr(user, "role", None) in ("ADMIN", "MANAGER"):
            return qs
        return qs.filter(created_by=user)

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

