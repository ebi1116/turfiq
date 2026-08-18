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

    def test_detail_displays_public_registration_link(self):
        self.owner.is_superuser=True;self.owner.save(update_fields=["is_superuser"])
        self.client.login(username="owner",password="pass")
        response=self.client.get(reverse("tournaments:detail",args=[self.t.pk]),secure=True)
        registration_path=reverse("tournaments:public-registration",args=[self.t.registration_token])
        self.assertContains(response,">Link</a>")
        self.assertContains(response,registration_path)

    def test_public_registration_closes_at_team_capacity(self):
        self.t.status="Registration Open";self.t.save(update_fields=["status"])
        url=reverse("tournaments:public-registration",args=[self.t.registration_token])
        self.assertContains(self.client.get(url),"Team details")
        for number in range(4,8):
            response=self.client.post(url,{"name":f"Public Team {number}","captain":"Captain","captain_mobile":f"90000000{number}","alternate_mobile":"","district":"Kochi","players":7,"jersey_color":"Green","consent":"on"})
            self.assertEqual(response.status_code,200)
        self.t.refresh_from_db()
        self.assertEqual(self.t.teams.count(),8)
        self.assertEqual(self.t.status,"Registration Closed")
        self.assertContains(self.client.get(url),"Registration Closed")

    def test_public_registration_rejects_duplicate_team_name(self):
        self.t.status="Registration Open";self.t.save(update_fields=["status"])
        response=self.client.post(reverse("tournaments:public-registration",args=[self.t.registration_token]),{"name":"Team 0","captain":"Other","captain_mobile":"999","alternate_mobile":"","district":"Kochi","players":7,"jersey_color":"Blue","consent":"on"})
        self.assertContains(response,"already registered")
        self.assertEqual(self.t.teams.count(),4)
