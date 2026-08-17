from decimal import Decimal
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
import uuid

class Tournament(models.Model):
    SPORTS=[(x,x) for x in ("Football","Cricket","Futsal","Volleyball","Custom")]
    STATUSES=[(x,x) for x in ("Draft","Registration Open","Registration Closed","Live","Completed")]
    FORMATS=[("single","Single Elimination"),("league","League")]
    owner=models.ForeignKey(User,on_delete=models.CASCADE,related_name="tournaments")
    name=models.CharField(max_length=150); sport=models.CharField(max_length=20,choices=SPORTS)
    banner=models.ImageField(upload_to="tournaments/",blank=True); start_date=models.DateField(); end_date=models.DateField()
    registration_deadline=models.DateField(); venue=models.CharField(max_length=180); description=models.TextField(blank=True)
    max_teams=models.PositiveIntegerField(default=8); entry_fee=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    prize_1=models.DecimalField(max_digits=12,decimal_places=2,default=0); prize_2=models.DecimalField(max_digits=12,decimal_places=2,default=0); prize_3=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    organizer=models.CharField(max_length=120); contact=models.CharField(max_length=20); rules=models.TextField(blank=True)
    status=models.CharField(max_length=25,choices=STATUSES,default="Draft",db_index=True); format=models.CharField(max_length=10,choices=FORMATS,default="single")
    registration_token=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["-start_date","name"]
    def __str__(self): return self.name
    @property
    def registration_is_open(self):
        from django.utils import timezone
        return self.status == "Registration Open" and self.registration_deadline >= timezone.localdate() and self.teams.count() < self.max_teams
    @property
    def expected_collection(self): return self.entry_fee*self.teams.count()
    @property
    def entry_collection(self): return self.teams.aggregate(v=Sum("payments__amount"))["v"] or Decimal("0")
    @property
    def pending_collection(self): return max(Decimal("0"),self.expected_collection-self.entry_collection)
    @property
    def total_income(self): return self.entry_collection+(self.incomes.aggregate(v=Sum("amount"))["v"] or Decimal("0"))
    @property
    def total_expenses(self): return self.expenses.aggregate(v=Sum("amount"))["v"] or Decimal("0")
    @property
    def net_profit(self): return self.total_income-self.total_expenses

class Team(models.Model):
    tournament=models.ForeignKey(Tournament,on_delete=models.CASCADE,related_name="teams")
    team_id=models.CharField(max_length=20,unique=True,blank=True); name=models.CharField(max_length=120)
    captain=models.CharField(max_length=120); captain_mobile=models.CharField(max_length=20); alternate_mobile=models.CharField(max_length=20,blank=True)
    district=models.CharField(max_length=100); players=models.PositiveIntegerField(default=1); jersey_color=models.CharField(max_length=40,blank=True)
    payment_status=models.CharField(max_length=10,choices=[("Paid","Paid"),("Pending","Pending")],default="Pending")
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["tournament","name"],name="unique_tournament_team")]; ordering=["name"]
    def save(self,*args,**kwargs):
        if not self.team_id:
            super().save(*args,**kwargs); self.team_id=f"T{self.tournament_id:04d}-{self.pk:04d}"; return super().save(update_fields=["team_id"])
        return super().save(*args,**kwargs)
    def __str__(self): return self.name
    @property
    def paid_amount(self): return self.payments.aggregate(v=Sum("amount"))["v"] or Decimal("0")

class Payment(models.Model):
    MODES=[(x,x) for x in ("Cash","UPI","Card","Bank Transfer","Online")]
    team=models.ForeignKey(Team,on_delete=models.CASCADE,related_name="payments"); amount=models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(0)])
    date=models.DateField(); mode=models.CharField(max_length=20,choices=MODES); transaction_id=models.CharField(max_length=100,blank=True); remarks=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def save(self,*args,**kwargs):
        super().save(*args,**kwargs); team=self.team; team.payment_status="Paid" if team.paid_amount>=team.tournament.entry_fee else "Pending"; team.save(update_fields=["payment_status"])

class Match(models.Model):
    STATUSES=[(x,x) for x in ("Upcoming","Live","Completed")]
    tournament=models.ForeignKey(Tournament,on_delete=models.CASCADE,related_name="matches"); number=models.PositiveIntegerField(); round=models.CharField(max_length=40,blank=True)
    date=models.DateField(null=True,blank=True); time=models.TimeField(null=True,blank=True); ground=models.CharField(max_length=100,blank=True)
    team_a=models.ForeignKey(Team,on_delete=models.SET_NULL,null=True,blank=True,related_name="matches_a"); team_b=models.ForeignKey(Team,on_delete=models.SET_NULL,null=True,blank=True,related_name="matches_b")
    referee=models.CharField(max_length=120,blank=True); score_a=models.PositiveIntegerField(default=0); score_b=models.PositiveIntegerField(default=0)
    wickets_a=models.PositiveIntegerField(default=0); wickets_b=models.PositiveIntegerField(default=0); overs_a=models.DecimalField(max_digits=4,decimal_places=1,default=0); overs_b=models.DecimalField(max_digits=4,decimal_places=1,default=0)
    winner=models.ForeignKey(Team,on_delete=models.SET_NULL,null=True,blank=True,related_name="wins"); status=models.CharField(max_length=12,choices=STATUSES,default="Upcoming")
    next_match=models.ForeignKey("self",on_delete=models.SET_NULL,null=True,blank=True,related_name="feeders"); next_slot=models.CharField(max_length=1,blank=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["tournament","number"],name="unique_tournament_match")]; ordering=["number"]
    def save(self,*args,**kwargs):
        if self.status=="Completed": self.winner=self.team_a if self.score_a>self.score_b else self.team_b if self.score_b>self.score_a else None
        super().save(*args,**kwargs)
        if self.winner and self.next_match_id:
            Match.objects.filter(pk=self.next_match_id).update(**({"team_a":self.winner} if self.next_slot=="A" else {"team_b":self.winner}))

class Standing(models.Model):
    tournament=models.ForeignKey(Tournament,on_delete=models.CASCADE,related_name="standings"); team=models.OneToOneField(Team,on_delete=models.CASCADE,related_name="standing")
    played=models.PositiveIntegerField(default=0); won=models.PositiveIntegerField(default=0); lost=models.PositiveIntegerField(default=0); drawn=models.PositiveIntegerField(default=0)
    goals_for=models.PositiveIntegerField(default=0); goals_against=models.PositiveIntegerField(default=0); points=models.PositiveIntegerField(default=0)
    @property
    def goal_difference(self): return self.goals_for-self.goals_against
    class Meta: ordering=["-points","-goals_for","team__name"]

class Income(models.Model):
    tournament=models.ForeignKey(Tournament,on_delete=models.CASCADE,related_name="incomes"); kind=models.CharField(max_length=20,choices=[("Sponsor","Sponsor"),("Other","Other")]); source=models.CharField(max_length=120); amount=models.DecimalField(max_digits=12,decimal_places=2); date=models.DateField()
class TournamentExpense(models.Model):
    CATEGORIES=[(x,x) for x in ("Ground Decoration","Referee","Water","Food","Marketing","Sound System","Electricity","Photography","Other")]
    tournament=models.ForeignKey(Tournament,on_delete=models.CASCADE,related_name="expenses"); category=models.CharField(max_length=30,choices=CATEGORIES); amount=models.DecimalField(max_digits=12,decimal_places=2); date=models.DateField(); notes=models.TextField(blank=True)
class Prize(models.Model):
    tournament=models.ForeignKey(Tournament,on_delete=models.CASCADE,related_name="prizes"); title=models.CharField(max_length=30,choices=[(x,x) for x in ("Champion","Runner Up","Second Runner","MVP","Best Goalkeeper","Top Scorer")]); recipient=models.CharField(max_length=120,blank=True); amount=models.DecimalField(max_digits=12,decimal_places=2,default=0); paid=models.BooleanField(default=False)
class Reminder(models.Model):
    tournament=models.ForeignKey(Tournament,on_delete=models.CASCADE,related_name="reminders"); kind=models.CharField(max_length=30,choices=[(x,x) for x in ("Registration Closing","Match Reminder","Final Match Reminder","Prize Distribution Reminder")]); due_at=models.DateTimeField(); is_done=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
