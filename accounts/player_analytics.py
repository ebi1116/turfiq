from collections import defaultdict
from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from .models import PlayerMatchRecord


PERIODS = {
    "week": ("This Week", 7),
    "month": ("This Month", 31),
    "quarter": ("Last 3 Months", 92),
    "all": ("All Time", None),
}


def _period_start(period, today):
    days = PERIODS[period][1]
    return today - timedelta(days=days - 1) if days else None


def _score(matches, metrics):
    """A transparent 100-point score using only fields present in match data."""
    if not metrics["matches"]:
        return None
    parts = [(min(metrics["matches"] / 12 * 15, 15), 15)]
    decided = metrics["wins"] + metrics["losses"]
    if decided:
        parts.append((metrics["wins"] / decided * 25, 25))
    # Goals and assists are recorded consistently (including meaningful zeroes).
    parts.append((min((metrics["goals"] + metrics["assists"]) / max(metrics["matches"], 1) * 15, 15), 15))
    rated = matches.filter(performance_rating__isnull=False).aggregate(value=Avg("performance_rating"))["value"]
    if rated is not None:
        parts.append((float(rated) * 4.5, 45))
    earned = sum(value for value, _weight in parts)
    possible = sum(weight for _value, weight in parts)
    return round(earned / possible * 100) if possible else None


def _metrics(matches):
    aggregate = matches.aggregate(
        matches=Count("id"), wins=Count("id", filter=Q(result="Won")),
        losses=Count("id", filter=Q(result="Lost")),
        goals=Sum("goals"), assists=Sum("assists"), rating=Avg("performance_rating"),
        runs=Sum("runs"), wickets=Sum("wickets"), catches=Sum("catches"),
        fifties=Count("id", filter=Q(runs__gte=50, runs__lt=100)),
        centuries=Count("id", filter=Q(runs__gte=100)),
    )
    values = {key: aggregate[key] or 0 for key in ("matches", "wins", "losses", "goals", "assists", "runs", "wickets", "catches", "fifties", "centuries")}
    values["rating"] = round(float(aggregate["rating"]), 1) if aggregate["rating"] is not None else None
    decided = values["wins"] + values["losses"]
    values["win_rate"] = round(values["wins"] / decided * 100) if decided else 0
    values["average_goals"] = round(values["goals"] / values["matches"], 1) if values["matches"] else 0
    values["average_assists"] = round(values["assists"] / values["matches"], 1) if values["matches"] else 0
    values["score"] = _score(matches, values)
    return values


def _trend(records):
    buckets = defaultdict(lambda: {"matches": 0, "goals": 0, "assists": 0, "wins": 0, "losses": 0, "ratings": []})
    for record in records:
        start = record.match_date - timedelta(days=record.match_date.weekday())
        item = buckets[start]
        item["matches"] += 1; item["goals"] += record.goals; item["assists"] += record.assists
        item["wins"] += record.result == "Won"; item["losses"] += record.result == "Lost"
        if record.performance_rating is not None: item["ratings"].append(float(record.performance_rating))
    result = []
    for date, item in sorted(buckets.items()):
        item["label"] = date.strftime("%d %b")
        item["rating"] = round(sum(item["ratings"]) / len(item["ratings"]), 1) if item["ratings"] else None
        result.append(item)
    return result


def _tournament_stats(user, records):
    """Return participation and verified tournament titles for a player."""
    from tournaments.models import Tournament

    team_ids = list(user.team_memberships.values_list("team_id", flat=True))
    record_tournament_ids = records.exclude(tournament__isnull=True).values_list("tournament_id", flat=True)
    tournaments = Tournament.objects.filter(Q(id__in=record_tournament_ids) | Q(teams__id__in=team_ids)).distinct()
    titles = 0
    for tournament in tournaments.filter(status="Completed"):
        final = tournament.matches.filter(status="Completed").order_by("-number").first()
        if final and final.winner_id in team_ids:
            titles += 1
    return {"participated": tournaments.count(), "won": titles}


def _current_form(records):
    results = list(records.order_by("-match_date", "-created_at").values_list("result", flat=True)[:5])
    if not results:
        return {"label": "No form yet", "detail": "Record a match to start your form guide.", "wins": 0, "total": 0}
    wins = results.count("Won")
    if wins >= 4:
        label = "Excellent form"
    elif wins >= 3:
        label = "In form"
    elif wins >= 1:
        label = "Building momentum"
    else:
        label = "Ready to bounce back"
    return {"label": label, "detail": f"{wins} win{'s' if wins != 1 else ''} in your last {len(results)} matches", "wins": wins, "total": len(results)}


def player_analytics(user, period="month"):
    period = period if period in PERIODS else "month"
    today = timezone.localdate()
    records = PlayerMatchRecord.objects.filter(player=user).select_related("tournament")
    all_metrics = _metrics(records)
    start = _period_start(period, today)
    selected = records.filter(match_date__gte=start) if start else records
    metrics = _metrics(selected)
    week = _metrics(records.filter(match_date__gte=today - timedelta(days=6)))
    month = _metrics(records.filter(match_date__gte=today - timedelta(days=30)))
    tournament_stats = _tournament_stats(user, records)

    insight = "Record your completed matches to unlock a personalised performance insight."
    if metrics["matches"]:
        if period != "all" and start:
            previous = _metrics(records.filter(match_date__gte=start - timedelta(days=PERIODS[period][1]), match_date__lt=start))
            if metrics["rating"] is not None and previous["rating"] is not None:
                insight = "Your performance rating is improving compared with the previous period." if metrics["rating"] > previous["rating"] else "You are performing consistently compared with the previous period."
            elif metrics["win_rate"] > previous["win_rate"]:
                insight = "Your win rate is improving compared with the previous period."
            else:
                insight = "Keep building consistency—every recorded match sharpens your trend."
        else:
            insight = "Your score combines match activity, results, goal contribution and recorded ratings."
    return {
        "period": period, "period_label": PERIODS[period][0], "metrics": metrics, "all_metrics": all_metrics,
        "week_metrics": week, "month_metrics": month, "records": selected.order_by("-match_date", "-created_at"),
        "recent_matches": records.order_by("-match_date", "-created_at")[:5], "trend": _trend(selected), "insight": insight,
        "tournament_stats": tournament_stats, "current_form": _current_form(records),
    }
