from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView
from django.views import View
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone

from business.views import SettingsView
from django.urls import reverse_lazy
from .adapters import role_login_redirect_url
from .models import GoogleUserProfile, PlayerProfile, CricketScorecard, PlayerPost
from .forms import PlayerProfileForm, PlayerPostForm
from tournaments.models import Tournament, Match, Team


class SignInPageView(TemplateView):
    template_name = "account/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(role_login_redirect_url(request.user))
        return super().dispatch(request, *args, **kwargs)



class ProfileView(SettingsView):
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")


class PlayerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "google_profile") or request.user.google_profile.role != GoogleUserProfile.Role.PLAYER:
            return redirect(role_login_redirect_url(request.user))
        return super().dispatch(request, *args, **kwargs)


class RoleSelectionView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/choose_role.html"
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, "google_profile") and request.user.google_profile.role:
            return redirect(role_login_redirect_url(request.user))
        return super().dispatch(request, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        role = request.POST.get("role")
        if role not in ("player", "owner"):
            messages.error(request, "Please choose an account type."); return redirect("choose-role")
        profile, _ = GoogleUserProfile.objects.get_or_create(user=request.user)
        profile.role = role; profile.save(update_fields=["role", "updated_at"])
        return redirect(role_login_redirect_url(request.user))


class AccountTypeSwitchView(LoginRequiredMixin, TemplateView):
    """Let an existing account enter either of its TurfIQ experiences."""
    template_name = "accounts/switch_account.html"

    def post(self, request, *args, **kwargs):
        role = request.POST.get("role")
        if role not in (GoogleUserProfile.Role.PLAYER, GoogleUserProfile.Role.OWNER):
            messages.error(request, "Please choose a valid account type.")
            return redirect("switch-account-type")
        profile, _ = GoogleUserProfile.objects.get_or_create(user=request.user)
        profile.role = role
        profile.save(update_fields=["role", "updated_at"])
        messages.success(request, "You are now in your %s workspace." % profile.get_role_display())
        return redirect(role_login_redirect_url(request.user))


class PlayerOnboardingView(PlayerRequiredMixin, TemplateView):
    template_name = "player/onboarding.html"
    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, "player_profile"):
            return redirect("player-dashboard")
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs): return {**super().get_context_data(**kwargs), "form": PlayerProfileForm(user=self.request.user)}
    def post(self, request, *args, **kwargs):
        form = PlayerProfileForm(request.POST, request.FILES, user=request.user)
        if form.is_valid(): form.save(request.user); return redirect("player-dashboard")
        return self.render_to_response({"form": form})


def player_stats(user):
    cards = CricketScorecard.objects.filter(player=user, match__status="Completed").select_related("match", "match__tournament")
    matches = cards.values("match_id").distinct().count()
    teams = user.team_memberships.values_list("team_id", flat=True)
    tournaments = Tournament.objects.filter(teams__id__in=teams).distinct()
    wins = Match.objects.filter(winner_id__in=teams, status="Completed", id__in=cards.values("match_id")).count()
    aggregate = cards.aggregate(runs=Sum("runs"), wickets=Sum("wickets"), catches=Sum("catches"), balls=Sum("balls"), conceded=Sum("runs_conceded"), overs=Sum("overs"))
    return {"matches": matches, "tournaments": tournaments.count(), "wins": wins, "cards": cards, "runs": aggregate["runs"] or 0, "wickets": aggregate["wickets"] or 0, "catches": aggregate["catches"] or 0, "balls": aggregate["balls"] or 0, "conceded": aggregate["conceded"] or 0, "overs": aggregate["overs"] or 0}


class PlayerDashboardView(PlayerRequiredMixin, TemplateView):
    template_name = "player/dashboard.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); profile = self.request.user.player_profile; stats = player_stats(self.request.user)
        nearby = Tournament.objects.filter(status="Registration Open", sport=profile.sport, venue__icontains=profile.location).order_by("start_date")
        ctx.update(profile=profile, stats=stats, nearby_tournaments=nearby[:4], recent_cards=stats["cards"].order_by("-match__date")[:4], posts=PlayerPost.objects.select_related("player").order_by("-created_at")[:3])
        return ctx


class PlayerProfileView(PlayerRequiredMixin, TemplateView):
    template_name = "player/profile.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); ctx.update(profile=self.request.user.player_profile, stats=player_stats(self.request.user), form=PlayerProfileForm(instance=self.request.user.player_profile, user=self.request.user)); return ctx
    def post(self, request, *args, **kwargs):
        form = PlayerProfileForm(request.POST, request.FILES, instance=request.user.player_profile, user=request.user)
        if form.is_valid(): form.save(request.user); messages.success(request, "Your player profile has been updated.")
        return redirect("player-profile")


class PlayerTournamentListView(PlayerRequiredMixin, TemplateView):
    template_name = "player/tournaments.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); p = self.request.user.player_profile; qs = Tournament.objects.filter(status__in=["Registration Open", "Live"], sport=p.sport)
        if self.request.GET.get("near") != "all": qs = qs.filter(venue__icontains=p.location)
        for key, field in (("format", "format"), ("sport", "sport")):
            if self.request.GET.get(key): qs = qs.filter(**{field: self.request.GET[key]})
        sort = self.request.GET.get("sort", "soon")
        qs = qs.order_by("-prize_1") if sort == "prize" else qs.order_by("-created_at") if sort == "recent" else qs.order_by("start_date")
        ctx.update(tournaments=qs, profile=p, formats=Tournament.FORMATS); return ctx


class PlayerTournamentDetailView(PlayerRequiredMixin, TemplateView):
    template_name = "player/tournament_detail.html"
    def get_context_data(self, **kwargs):
        t = get_object_or_404(Tournament, pk=kwargs["pk"]); ctx = super().get_context_data(**kwargs)
        standings = t.standings.select_related("team").order_by("-points", "-goals_for")
        ctx.update(tournament=t, matches=t.matches.select_related("team_a", "team_b", "winner"), standings=standings, teams=t.teams.all()); return ctx


class PlayerMatchesView(PlayerRequiredMixin, TemplateView):
    template_name = "player/matches.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); cards = player_stats(self.request.user)["cards"].order_by("-match__date")
        result = self.request.GET.get("result")
        if result == "won": cards = cards.filter(match__winner_id__in=self.request.user.team_memberships.values("team_id"))
        elif result == "lost": cards = cards.exclude(match__winner_id__in=self.request.user.team_memberships.values("team_id")).filter(match__status="Completed")
        ctx["cards"] = cards; return ctx


class PlayerScorecardView(PlayerRequiredMixin, TemplateView):
    template_name = "player/scorecard.html"
    def get_context_data(self, **kwargs):
        match = get_object_or_404(Match.objects.select_related("tournament", "team_a", "team_b", "winner"), pk=kwargs["pk"])
        cards = match.cricket_scorecards.select_related("player", "team").all(); ctx = super().get_context_data(**kwargs)
        ctx.update(match=match, team_a_cards=cards.filter(team=match.team_a), team_b_cards=cards.filter(team=match.team_b)); return ctx


class PlayerPostsView(PlayerRequiredMixin, TemplateView):
    template_name = "player/posts.html"
    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "form": PlayerPostForm(), "posts": PlayerPost.objects.select_related("player", "tournament").order_by("-created_at")}
    def post(self, request, *args, **kwargs):
        form = PlayerPostForm(request.POST, request.FILES)
        if form.is_valid(): post = form.save(commit=False); post.player = request.user; post.save(); messages.success(request, "Your sports post is live."); return redirect("player-posts")
        return self.render_to_response({"form": form, "posts": PlayerPost.objects.order_by("-created_at")})
