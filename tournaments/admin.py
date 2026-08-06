from django.contrib import admin
from .models import Tournament,Team,Payment,Match,Standing,Income,TournamentExpense,Prize,Reminder

for model in (Tournament,Team,Payment,Match,Standing,Income,TournamentExpense,Prize,Reminder): admin.site.register(model)
