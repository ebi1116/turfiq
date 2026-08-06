import random
from django.db import transaction
from .models import Match,Standing

@transaction.atomic
def generate_fixtures(tournament,mode="random"):
    teams=list(tournament.teams.all()); Match.objects.filter(tournament=tournament).delete()
    if mode=="random": random.shuffle(teams)
    if tournament.format=="league":
        n=1
        for i,a in enumerate(teams):
            for b in teams[i+1:]: Match.objects.create(tournament=tournament,number=n,round="League",team_a=a,team_b=b); n+=1
        Standing.objects.bulk_create([Standing(tournament=tournament,team=t) for t in teams],ignore_conflicts=True)
    else:
        if len(teams)<2: return 0
        size=1
        while size<len(teams): size*=2
        teams += [None]*(size-len(teams)); rounds=[]; count=size//2; number=1
        labels={8:"Quarter Final",4:"Semi Final",2:"Final"}
        while count:
            current=[]
            for _ in range(count): current.append(Match.objects.create(tournament=tournament,number=number,round=labels.get(count,f"Round of {count*2}"))); number+=1
            rounds.append(current); count//=2
        for i in range(len(rounds)-1):
            for j,m in enumerate(rounds[i]): m.next_match=rounds[i+1][j//2]; m.next_slot="A" if j%2==0 else "B"; m.save(update_fields=["next_match","next_slot"])
        for i,m in enumerate(rounds[0]):
            m.team_a=teams[i*2]; m.team_b=teams[i*2+1]; m.save(update_fields=["team_a","team_b"])
    return Match.objects.filter(tournament=tournament).count()

@transaction.atomic
def rebuild_standings(tournament):
    Standing.objects.filter(tournament=tournament).delete()
    rows={t.pk:Standing(tournament=tournament,team=t) for t in tournament.teams.all()}
    for m in tournament.matches.filter(status="Completed",team_a__isnull=False,team_b__isnull=False):
        a,b=rows[m.team_a_id],rows[m.team_b_id]; a.played+=1;b.played+=1;a.goals_for+=m.score_a;a.goals_against+=m.score_b;b.goals_for+=m.score_b;b.goals_against+=m.score_a
        if m.score_a>m.score_b:a.won+=1;a.points+=3;b.lost+=1
        elif m.score_b>m.score_a:b.won+=1;b.points+=3;a.lost+=1
        else:a.drawn+=1;b.drawn+=1;a.points+=1;b.points+=1
    Standing.objects.bulk_create(rows.values()); return rows.values()
