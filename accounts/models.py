from django.conf import settings
from django.db import models


class GoogleUserProfile(models.Model):
    class Role(models.TextChoices):
        PLAYER = "player", "Player"
        OWNER = "owner", "Owner"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_profile",
    )
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_picture = models.URLField(max_length=1000, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Google user"
        verbose_name_plural = "Google users"

    def __str__(self):
        return self.user.get_full_name() or self.user.email or str(self.user)


class PlayerProfile(models.Model):
    SPORTS = [("Cricket", "Cricket"), ("Football", "Football"), ("Futsal", "Futsal"), ("Volleyball", "Volleyball")]
    SKILL_LEVELS = [(x, x) for x in ("Beginner", "Intermediate", "Advanced", "Professional")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="player_profile")
    photo = models.ImageField(upload_to="players/", blank=True)
    mobile_number = models.CharField(max_length=20)
    location = models.CharField(max_length=120, db_index=True)
    sport = models.CharField(max_length=30, choices=SPORTS, default="Cricket")
    position = models.CharField(max_length=100)
    skill_level = models.CharField(max_length=30, choices=SKILL_LEVELS)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    favourite_team = models.CharField(max_length=120, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class PlayerTeam(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships")
    team = models.ForeignKey("tournaments.Team", on_delete=models.CASCADE, related_name="player_memberships")
    class Meta:
        constraints = [models.UniqueConstraint(fields=["player", "team"], name="unique_player_team")]


class CricketScorecard(models.Model):
    match = models.ForeignKey("tournaments.Match", on_delete=models.CASCADE, related_name="cricket_scorecards")
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cricket_scorecards")
    team = models.ForeignKey("tournaments.Team", on_delete=models.SET_NULL, null=True, blank=True, related_name="scorecards")
    runs = models.PositiveIntegerField(default=0); balls = models.PositiveIntegerField(default=0)
    fours = models.PositiveIntegerField(default=0); sixes = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0); overs = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    runs_conceded = models.PositiveIntegerField(default=0); catches = models.PositiveIntegerField(default=0)
    dismissal = models.CharField(max_length=180, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["match", "player"], name="unique_match_player_scorecard")]

    @property
    def strike_rate(self): return round((self.runs / self.balls * 100), 1) if self.balls else 0
    @property
    def economy(self): return round((self.runs_conceded / float(self.overs)), 2) if self.overs else 0


class PlayerPost(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sports_posts")
    image = models.ImageField(upload_to="posts/", blank=True)
    video = models.FileField(upload_to="posts/", blank=True)
    caption = models.TextField(max_length=1000)
    sport = models.CharField(max_length=30, default="Cricket")
    tournament = models.ForeignKey("tournaments.Tournament", on_delete=models.SET_NULL, null=True, blank=True, related_name="player_posts")
    turf_tag = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
