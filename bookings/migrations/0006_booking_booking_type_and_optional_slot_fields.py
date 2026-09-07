from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("bookings", "0005_customer_unique_owner_customer_name_ci")]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="booking_type",
            field=models.CharField(choices=[("DAY", "Day Wise"), ("SLOT", "Time / Slot Wise")], db_index=True, default="SLOT", max_length=4),
        ),
        migrations.AlterField(model_name="booking", name="booking_time", field=models.TimeField(blank=True, null=True)),
        migrations.AlterField(model_name="booking", name="duration", field=models.DecimalField(blank=True, decimal_places=1, help_text="Duration in hours", max_digits=4, null=True)),
    ]
