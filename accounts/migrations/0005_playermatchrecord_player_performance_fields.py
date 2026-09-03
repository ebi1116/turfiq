# Generated manually to include the previously introduced player match record.
import django.db.models.deletion
import django.core.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_alter_googleuserprofile_role_playerpost_and_more"),
        ("tournaments", "0002_tournament_registration_token"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PlayerMatchRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sport", models.CharField(default="Cricket", max_length=30)),
                ("team_name", models.CharField(max_length=120)),
                ("opponent_name", models.CharField(max_length=120)),
                ("match_date", models.DateField(db_index=True)),
                ("venue", models.CharField(blank=True, max_length=150)),
                ("result", models.CharField(choices=[("Won", "Won"), ("Lost", "Lost"), ("Draw", "Draw / Tie")], max_length=10)),
                ("goals", models.PositiveIntegerField(default=0)),
                ("assists", models.PositiveIntegerField(default=0)),
                ("performance_rating", models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ("runs", models.PositiveIntegerField(default=0)),
                ("balls", models.PositiveIntegerField(default=0)),
                ("wickets", models.PositiveIntegerField(default=0)),
                ("catches", models.PositiveIntegerField(default=0)),
                ("notes", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("player", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="match_records", to=settings.AUTH_USER_MODEL)),
                ("tournament", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="player_match_records", to="tournaments.tournament")),
            ],
            options={"ordering": ("-match_date", "-created_at")},
        ),
    ]
