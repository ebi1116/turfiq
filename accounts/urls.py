from django.urls import path
from . import views

urlpatterns = [
    path("choose-role/", views.RoleSelectionView.as_view(), name="choose-role"),
    path("player/onboarding/", views.PlayerOnboardingView.as_view(), name="player-onboarding"),
    path("player/", views.PlayerDashboardView.as_view(), name="player-dashboard"),
    path("player/profile/", views.PlayerProfileView.as_view(), name="player-profile"),
    path("player/tournaments/", views.PlayerTournamentListView.as_view(), name="player-tournaments"),
    path("player/tournaments/<int:pk>/", views.PlayerTournamentDetailView.as_view(), name="player-tournament-detail"),
    path("player/matches/", views.PlayerMatchesView.as_view(), name="player-matches"),
    path("player/scorecards/<int:pk>/", views.PlayerScorecardView.as_view(), name="player-scorecard"),
    path("player/posts/", views.PlayerPostsView.as_view(), name="player-posts"),
]
