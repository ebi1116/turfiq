from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("bookings", "0002_ground_relationship"), ("business", "0005_ground_operating_hours"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="BlockedSlot", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("start_at", models.DateTimeField(db_index=True)), ("end_at", models.DateTimeField(db_index=True)),
            ("reason", models.CharField(blank=True, max_length=200)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("ground", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="blocked_slots", to="business.ground")),
            ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="blocked_slots", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ("start_at",)}),
        migrations.AddConstraint(model_name="blockedslot", constraint=models.CheckConstraint(condition=models.Q(end_at__gt=models.F("start_at")), name="blocked_slot_positive_duration")),
    ]
