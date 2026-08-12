from django.db import migrations, models
import django.db.models.deletion


def attach_existing_bookings(apps, schema_editor):
    Booking = apps.get_model("bookings", "Booking")
    Settings = apps.get_model("business", "BusinessSettings")
    Ground = apps.get_model("business", "Ground")
    for owner_id in Booking.objects.values_list("owner_id", flat=True).distinct():
        settings, _ = Settings.objects.get_or_create(owner_id=owner_id)
        names = list(Booking.objects.filter(owner_id=owner_id).values_list("legacy_ground", flat=True).distinct())
        if not names:
            names = [""]
        settings.number_of_grounds = len(names)
        settings.save(update_fields=("number_of_grounds",))
        for number, name in enumerate(names, 1):
            ground, _ = Ground.objects.get_or_create(owner_id=owner_id, turf=settings, number=number, defaults={"name": name or ""})
            Booking.objects.filter(owner_id=owner_id, legacy_ground=name).update(ground=ground)


class Migration(migrations.Migration):
    dependencies = [("business", "0004_profile_and_grounds"), ("bookings", "0001_initial")]
    operations = [
        migrations.RenameField(model_name="booking", old_name="ground", new_name="legacy_ground"),
        migrations.AddField(model_name="booking", name="ground", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="business.ground")),
        migrations.RunPython(attach_existing_bookings, migrations.RunPython.noop),
        migrations.RemoveField(model_name="booking", name="legacy_ground"),
        migrations.AlterField(model_name="booking", name="ground", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="business.ground")),
    ]
