import csv
from datetime import timedelta
from io import BytesIO
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count,Sum,Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from django.urls import reverse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .forms import *
from .models import *
from .services import generate_fixtures,rebuild_standings,register_team
from django.core.exceptions import ValidationError

def owned(request,pk): return get_object_or_404(Tournament,pk=pk,owner=request.user)
@login_required
def dashboard(request):
    qs=Tournament.objects.filter(owner=request.user).annotate(team_count=Count("teams",distinct=True),match_count=Count("matches",distinct=True))
    q=request.GET.get("q",""); sport=request.GET.get("sport",""); status=request.GET.get("status",""); year=request.GET.get("year","")
    if q: qs=qs.filter(name__icontains=q)
    if sport: qs=qs.filter(sport=sport)
    if status: qs=qs.filter(status=status)
    if year: qs=qs.filter(start_date__year=year)
    all_qs=Tournament.objects.filter(owner=request.user)
    prize_totals=all_qs.aggregate(a=Sum("prize_1"),b=Sum("prize_2"),c=Sum("prize_3"))
    ctx={"tournaments":qs,"total":all_qs.count(),"upcoming":all_qs.filter(start_date__gt=timezone.localdate()).count(),"live":all_qs.filter(status="Live").count(),"completed":all_qs.filter(status="Completed").count(),"teams":Team.objects.filter(tournament__owner=request.user).count(),"matches":Match.objects.filter(tournament__owner=request.user).count(),"prizes":sum((prize_totals[x] or 0 for x in ("a","b","c")),Decimal("0")),"sports":Tournament.SPORTS,"statuses":Tournament.STATUSES}
    ctx["collection"]=sum((t.entry_collection for t in all_qs),Decimal("0"));ctx["profit"]=sum((t.net_profit for t in all_qs),Decimal("0"));ctx["activities"]=Team.objects.filter(tournament__owner=request.user).select_related("tournament").order_by("-created_at")[:6]
    return render(request,"tournaments/dashboard.html",ctx)
@login_required
def tournament_form(request,pk=None):
    obj=owned(request,pk) if pk else None; form=TournamentForm(request.POST or None,request.FILES or None,instance=obj)
    if form.is_valid():
        item=form.save(commit=False);item.owner=request.user;item.save()
        registration_url=request.build_absolute_uri(reverse("tournaments:public-registration",args=[item.registration_token]))
        messages.success(request,f"Tournament saved. Public registration form: {registration_url}")
        return redirect("tournaments:detail",pk=item.pk)
    return render(request,"tournaments/form.html",{"form":form,"object":obj,"title":"Edit tournament" if obj else "Create tournament"})
@login_required
def detail(request,pk):
    t=owned(request,pk); standings=list(t.standings.select_related("team"));standings.sort(key=lambda x:(x.points,x.goal_difference,x.goals_for),reverse=True)
    return render(request,"tournaments/detail.html",{"tournament":t,"standings":standings,"due_reminders":t.reminders.filter(is_done=False,due_at__lte=timezone.now()+timedelta(days=7)),"income_chart":[float(t.entry_collection),float(t.incomes.aggregate(v=Sum("amount"))["v"] or 0),float(t.total_expenses)]})
@login_required
def delete(request,pk):
    t=owned(request,pk)
    if request.method=="POST":t.delete();messages.success(request,"Tournament deleted.");return redirect("tournaments:dashboard")
    return render(request,"shared/confirm_delete.html",{"object":t})
@login_required
def team_form(request,pk):
    t=owned(request,pk); form=TeamForm(request.POST or None)
    if form.is_valid():
        if t.teams.count()>=t.max_teams: form.add_error(None,"Maximum team capacity reached.")
        else:item=form.save(commit=False);item.tournament=t;item.save();messages.success(request,f"Team registered as {item.team_id}.");return redirect("tournaments:detail",pk=pk)
    return render(request,"tournaments/form.html",{"form":form,"title":"Register team","object":t})

def public_registration(request, token):
    t=get_object_or_404(Tournament,registration_token=token)
    form=PublicTeamRegistrationForm(request.POST or None)
    registered_team=None
    if request.method == "POST" and form.is_valid():
        try:
            registered_team=register_team(t,form.cleaned_data.copy())
            t.refresh_from_db()
            form=PublicTeamRegistrationForm()
        except ValidationError as error:
            form.add_error(None,error.message)
    return render(request,"tournaments/public_registration.html",{"tournament":t,"form":form,"registered_team":registered_team})
@login_required
def payment_form(request,pk,team_pk):
    t=owned(request,pk);team=get_object_or_404(t.teams,pk=team_pk);form=PaymentForm(request.POST or None)
    if form.is_valid():item=form.save(commit=False);item.team=team;item.save();messages.success(request,"Payment recorded.");return redirect("tournaments:detail",pk=pk)
    return render(request,"tournaments/form.html",{"form":form,"title":f"Payment · {team.name}","object":t})
@login_required
def fixtures(request,pk):
    t=owned(request,pk)
    if request.method=="POST": count=generate_fixtures(t,request.POST.get("mode","random"));messages.success(request,f"Generated {count} fixtures.")
    return redirect("tournaments:detail",pk=pk)
@login_required
def match_form(request,pk,match_pk=None):
    t=owned(request,pk);obj=get_object_or_404(t.matches,pk=match_pk) if match_pk else None;form=MatchForm(request.POST or None,instance=obj,tournament=t)
    if form.is_valid():item=form.save(commit=False);item.tournament=t;item.number=obj.number if obj else (t.matches.aggregate(v=Max("number"))["v"] or 0)+1;item.save();rebuild_standings(t);messages.success(request,"Match updated.");return redirect("tournaments:detail",pk=pk)
    return render(request,"tournaments/form.html",{"form":form,"title":"Update match" if obj else "Manual fixture","object":t})
FORMS={"income":IncomeForm,"expense":ExpenseForm,"prize":PrizeForm,"reminder":ReminderForm}
@login_required
def generic_form(request,pk,kind):
    t=owned(request,pk);klass=FORMS.get(kind)
    if not klass:return redirect("tournaments:detail",pk=pk)
    form=klass(request.POST or None)
    if form.is_valid():item=form.save(commit=False);item.tournament=t;item.save();messages.success(request,f"{kind.title()} saved.");return redirect("tournaments:detail",pk=pk)
    return render(request,"tournaments/form.html",{"form":form,"title":f"Add {kind}","object":t})
@login_required
def export_report(request,pk,fmt):
    t=owned(request,pk);rows=[["Team ID","Team","Captain","Mobile","Paid"],*[[x.team_id,x.name,x.captain,x.captain_mobile,str(x.paid_amount)] for x in t.teams.all()]]
    if fmt=="xlsx":
        wb=Workbook();ws=wb.active;ws.title="Teams";[ws.append(r) for r in rows];buf=BytesIO();wb.save(buf);data=buf.getvalue();ctype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif fmt=="pdf":
        buf=BytesIO();p=canvas.Canvas(buf,pagesize=A4);p.drawString(50,800,f"{t.name} - Tournament Summary");y=775
        for row in rows:p.drawString(50,y," | ".join(row));y-=18
        p.save();data=buf.getvalue();ctype="application/pdf"
    else:
        out=HttpResponse(content_type="text/csv");out["Content-Disposition"]=f'attachment; filename="{t.pk}-teams.csv"';w=csv.writer(out);w.writerows(rows);return out
    out=HttpResponse(data,content_type=ctype);out["Content-Disposition"]=f'attachment; filename="{t.pk}-report.{fmt}"';return out
