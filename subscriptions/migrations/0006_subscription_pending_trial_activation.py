from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0005_free_30_day_trial")]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="status",
            field=models.CharField(db_index=True, default="pending", max_length=30),
        ),
    ]
