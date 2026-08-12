from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("business", "0003_turfownerworkspace")]
    operations = [
        migrations.AddField(model_name="businesssettings", name="owner_name", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="businesssettings", name="phone_number", field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name="businesssettings", name="address", field=models.TextField(blank=True)),
        migrations.AddField(model_name="businesssettings", name="number_of_grounds", field=models.PositiveIntegerField(default=1)),
        migrations.CreateModel(
            name="Ground",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveIntegerField()),
                ("name", models.CharField(blank=True, max_length=120)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grounds", to="auth.user")),
                ("turf", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grounds", to="business.businesssettings")),
            ],
            options={"ordering": ("number",)},
        ),
        migrations.AddConstraint(model_name="ground", constraint=models.UniqueConstraint(fields=("turf", "number"), name="unique_turf_ground_number")),
    ]
