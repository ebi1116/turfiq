from django import forms
from .models import Tournament,Team,Payment,Match,Income,TournamentExpense,Prize,Reminder

class StyledForm(forms.ModelForm):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        for f in self.fields.values(): f.widget.attrs["class"]="form-check-input" if isinstance(f.widget,forms.CheckboxInput) else "form-select" if isinstance(f.widget,forms.Select) else "form-control"

class TournamentForm(StyledForm):
    class Meta:
        model=Tournament; exclude=("owner",)
        widgets={"start_date":forms.DateInput(attrs={"type":"date"}),"end_date":forms.DateInput(attrs={"type":"date"}),"registration_deadline":forms.DateInput(attrs={"type":"date"}),"description":forms.Textarea(attrs={"rows":3}),"rules":forms.Textarea(attrs={"rows":4})}
    def clean(self):
        d=super().clean()
        if d.get("start_date") and d.get("end_date") and d["end_date"]<d["start_date"]: self.add_error("end_date","End date must be after start date.")
        if d.get("registration_deadline") and d.get("start_date") and d["registration_deadline"]>d["start_date"]: self.add_error("registration_deadline","Registration must close by the start date.")
        return d
class TeamForm(StyledForm):
    class Meta: model=Team; exclude=("tournament","team_id","payment_status")

class PublicTeamRegistrationForm(TeamForm):
    consent=forms.BooleanField(label="I confirm that the details entered are correct")
class PaymentForm(StyledForm):
    class Meta: model=Payment; exclude=("team",); widgets={"date":forms.DateInput(attrs={"type":"date"})}
class MatchForm(StyledForm):
    class Meta: model=Match; exclude=("tournament","number","winner","next_match","next_slot"); widgets={"date":forms.DateInput(attrs={"type":"date"}),"time":forms.TimeInput(attrs={"type":"time"})}
    def __init__(self,*a,tournament=None,**kw):
        super().__init__(*a,**kw)
        if tournament:
            self.fields["team_a"].queryset=tournament.teams.all(); self.fields["team_b"].queryset=tournament.teams.all()
class IncomeForm(StyledForm):
    class Meta: model=Income; exclude=("tournament",); widgets={"date":forms.DateInput(attrs={"type":"date"})}
class ExpenseForm(StyledForm):
    class Meta: model=TournamentExpense; exclude=("tournament",); widgets={"date":forms.DateInput(attrs={"type":"date"})}
class PrizeForm(StyledForm):
    class Meta: model=Prize; exclude=("tournament",)
class ReminderForm(StyledForm):
    class Meta: model=Reminder; exclude=("tournament","is_done"); widgets={"due_at":forms.DateTimeInput(attrs={"type":"datetime-local"})}
