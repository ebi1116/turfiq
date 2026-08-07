from django.db import migrations


def set_production_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(
        id=1,
        defaults={"domain": "turfiq.onrender.com", "name": "TurfIQ"},
    )


def reset_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(
        id=1,
        defaults={"domain": "example.com", "name": "example.com"},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("accounts", "0002_alter_googleuserprofile_options"),
    ]

    operations = [
        migrations.RunPython(set_production_site, reset_site),
    ]
