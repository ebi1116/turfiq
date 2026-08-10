import django.utils.timezone
import subscriptions.models
from django.db import migrations, models


def disable_unpaid_trials(apps, schema_editor):
    Subscription = apps.get_model("subscriptions", "Subscription")
    Subscription.objects.filter(status="trialing").update(
        status="inactive",
        trial_end=django.utils.timezone.now(),
    )


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0002_subscription_trial_end_subscription_trial_start_and_more")]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="status",
            field=models.CharField(db_index=True, default="inactive", max_length=30),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="trial_end",
            field=models.DateTimeField(default=subscriptions.models.default_trial_end),
        ),
        migrations.RunPython(disable_unpaid_trials, migrations.RunPython.noop),
    ]
