from django.urls import path
from . import views
app_name="tournaments"
urlpatterns=[
 path("register/<uuid:token>/",views.public_registration,name="public-registration"),
 path("",views.dashboard,name="dashboard"),path("new/",views.tournament_form,name="create"),path("<int:pk>/",views.detail,name="detail"),path("<int:pk>/edit/",views.tournament_form,name="edit"),path("<int:pk>/delete/",views.delete,name="delete"),
 path("<int:pk>/teams/new/",views.team_form,name="team-add"),path("<int:pk>/teams/<int:team_pk>/pay/",views.payment_form,name="payment-add"),path("<int:pk>/fixtures/",views.fixtures,name="fixtures"),path("<int:pk>/matches/new/",views.match_form,name="match-add"),path("<int:pk>/matches/<int:match_pk>/",views.match_form,name="match-edit"),
 path("<int:pk>/<str:kind>/new/",views.generic_form,name="generic-add"),path("<int:pk>/export/<str:fmt>/",views.export_report,name="export")]
