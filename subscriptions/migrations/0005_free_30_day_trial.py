from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone

import subscriptions.models


def start_free_trials(apps, schema_editor):
    Subscription = apps.get_model("subscriptions", "Subscription")
    now = timezone.now()
    Subscription.objects.filter(status="inactive").update(
        status="trialing",
        trial_start=now,
        trial_end=now + timedelta(days=30),
        current_start=None,
        current_end=None,
    )


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0004_restore_authorized_trial_window")]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="status",
            field=models.CharField(db_index=True, default="trialing", max_length=30),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="trial_end",
            field=models.DateTimeField(default=subscriptions.models.default_trial_end),
        ),
        migrations.RunPython(start_free_trials, migrations.RunPython.noop),
    ]
