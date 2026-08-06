from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Tournament,Team,Payment,Income,TournamentExpense
from .services import generate_fixtures

class TournamentTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user("owner",password="pass")
        self.other=User.objects.create_user("other",password="pass")
        self.t=Tournament.objects.create(owner=self.owner,name="Champions Cup",sport="Football",start_date=date(2027,1,10),end_date=date(2027,1,12),registration_deadline=date(2027,1,9),venue="Arena",max_teams=8,entry_fee=1000,organizer="Owner",contact="123",format="single")
        self.teams=[Team.objects.create(tournament=self.t,name=f"Team {i}",captain="Cap",captain_mobile="123",district="Kochi",players=7) for i in range(4)]
    def test_team_id_payment_and_financial_totals(self):
        team=self.teams[0];self.assertTrue(team.team_id.startswith(f"T{self.t.pk:04d}-"))
        Payment.objects.create(team=team,amount=1000,date=date.today(),mode="Cash");team.refresh_from_db();self.assertEqual(team.payment_status,"Paid")
        Income.objects.create(tournament=self.t,kind="Sponsor",source="Acme",amount=500,date=date.today())
        TournamentExpense.objects.create(tournament=self.t,category="Water",amount=200,date=date.today())
        self.assertEqual(self.t.entry_collection,Decimal("1000"));self.assertEqual(self.t.pending_collection,Decimal("3000"));self.assertEqual(self.t.net_profit,Decimal("1300"))
    def test_knockout_generation_and_advancement(self):
        self.assertEqual(generate_fixtures(self.t),3);first=self.t.matches.order_by("number").first();first.score_a=2;first.score_b=1;first.status="Completed";first.save();first.refresh_from_db();first.next_match.refresh_from_db();self.assertEqual(first.next_match.team_a,first.winner)
    def test_owner_isolation_and_dashboard(self):
        self.client.login(username="other",password="pass");self.assertEqual(self.client.get(reverse("tournaments:detail",args=[self.t.pk])).status_code,404)
        self.client.login(username="owner",password="pass");response=self.client.get(reverse("tournaments:dashboard"));self.assertContains(response,"Champions Cup")
