import subscriptions.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0003_require_account_premium")]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="trial_end",
            field=models.DateTimeField(default=subscriptions.models.default_trial_end),
        ),
    ]
