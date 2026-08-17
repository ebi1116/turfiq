from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("business", "0004_profile_and_grounds")]
    operations = [
        migrations.AddField(model_name="ground", name="use_custom_hours", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="ground", name="is_24_hours", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="ground", name="opening_time", field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name="ground", name="closing_time", field=models.TimeField(blank=True, null=True)),
    ]
