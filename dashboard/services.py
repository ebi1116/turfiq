from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from bookings.models import Booking
from expenses.models import Expense
from business.models import BusinessSettings, Ground

ZERO = Decimal("0")
def pct(current, previous):
    return round(float((current - previous) / previous * 100), 1) if previous else (100.0 if current else 0.0)
def total(qs): return qs.aggregate(v=Sum("amount"))["v"] or ZERO

def date_bounds(request):
    today = timezone.localdate(); preset = request.GET.get("range", "this_month")
    bounds = {
        "today": (today, today), "yesterday": (today-timedelta(days=1), today-timedelta(days=1)),
        "7days": (today-timedelta(days=6), today), "30days": (today-timedelta(days=29), today),
        "this_month": (today.replace(day=1), today), "last_month": ((today.replace(day=1)-timedelta(days=1)).replace(day=1), today.replace(day=1)-timedelta(days=1)),
        "this_year": (today.replace(month=1, day=1), today),
    }
    if preset == "custom":
        try: return datetime.strptime(request.GET["start"], "%Y-%m-%d").date(), datetime.strptime(request.GET["end"], "%Y-%m-%d").date(), preset
        except (KeyError, ValueError): pass
    start, end = bounds.get(preset, bounds["this_month"])
    return start, end, preset

def build_dashboard(user, ground=None):
    today = timezone.localdate(); week_start = today-timedelta(days=today.weekday()); month_start=today.replace(day=1)
    last_month_end=month_start-timedelta(days=1); last_month_start=last_month_end.replace(day=1)
    all_bookings = Booking.objects.filter(owner=user)
    if ground is not None:
        all_bookings = all_bookings.filter(ground=ground)
    qs=all_bookings.exclude(status="Cancelled"); expenses=Expense.objects.filter(owner=user)
    rev=lambda a,b: total(qs.filter(booking_date__range=(a,b)))
    exp=lambda a,b: total(expenses.filter(expense_date__range=(a,b)))
    today_r=rev(today,today); yesterday_r=rev(today-timedelta(days=1),today-timedelta(days=1))
    week_r=rev(week_start,today); last_week_r=rev(week_start-timedelta(days=7),week_start-timedelta(days=1))
    month_r=rev(month_start,today); last_month_r=rev(last_month_start,last_month_end)
    total_r=total(qs); total_e=total(expenses); net=total_r-total_e
    completed=all_bookings.filter(status="Completed").count(); cancelled=all_bookings.filter(status="Cancelled").count(); count=all_bookings.count()
    confirmed=all_bookings.filter(status__in=("Confirmed", "Pending"), booking_date__gte=today).count()
    today_count=all_bookings.filter(booking_date=today).count()
    customer_counts=all_bookings.values("customer").annotate(n=Count("id")); returning=customer_counts.filter(n__gt=1).count(); customers=customer_counts.count()
    settings=BusinessSettings.objects.get_or_create(owner=user)[0]; work_hours=max((datetime.combine(today,settings.closing_time)-datetime.combine(today,settings.opening_time)).seconds/3600,1)
    capacity_grounds = 1 if ground else max(Ground.objects.filter(owner=user, is_active=True).count(), 1)
    booked=float(qs.filter(booking_date__range=(month_start,today)).aggregate(v=Sum("duration"))["v"] or 0); available=work_hours*max(today.day,1)*capacity_grounds; occupancy=min(booked/available*100,100)
    cards=[
        ("Total Grounds",capacity_grounds,0,"active playing grounds","layer-group"),
        ("Today's Revenue",today_r,pct(today_r,yesterday_r),"vs yesterday","wallet"), ("This Week",week_r,pct(week_r,last_week_r),"vs last week","calendar-week"),
        ("This Month",month_r,pct(month_r,last_month_r),"vs last month","chart-line"), ("Total Revenue",total_r,0,"all-time earnings","coins"),
        ("Total Bookings",count,0,"all bookings","calendar-check"), ("Today's Bookings",today_count,0,"scheduled today","calendar-day"),
        ("Upcoming Bookings",confirmed,0,"confirmed or pending","clock"), ("Completed",completed,0,"successful bookings","circle-check"),
        ("Cancelled",cancelled,round(cancelled/count*100,1) if count else 0,"cancellation rate","ban"), ("Active Customers",customers,0,"unique customers","users"),
        ("Returning",returning,round(returning/customers*100,1) if customers else 0,"repeat customers","user-clock"), ("Occupancy",round(occupancy,1),0,"available capacity used","gauge-high"),
        ("Expenses",total_e,0,"all-time outflow","receipt"), ("Net Income",net,0,"revenue minus expenses","sack-dollar"),
    ]
    # Last 30 days powers the daily trend and keeps the chart readable.
    days=[today-timedelta(days=i) for i in range(29,-1,-1)]; daily_map={r["booking_date"]:r["v"] for r in qs.filter(booking_date__gte=days[0]).values("booking_date").annotate(v=Sum("amount"))}
    daily_count_map={r["booking_date"]:r["v"] for r in all_bookings.filter(booking_date__gte=days[0]).values("booking_date").annotate(v=Count("id"))}
    monthly=list(qs.filter(booking_date__gte=today-timedelta(days=365)).annotate(period=TruncMonth("booking_date")).values("period").annotate(v=Sum("amount")).order_by("period"))
    monthly_counts=list(all_bookings.filter(booking_date__gte=today-timedelta(days=365)).annotate(period=TruncMonth("booking_date")).values("period").annotate(v=Count("id")).order_by("period"))
    payment=list(qs.values("payment_method").annotate(v=Count("id"))); sports=list(qs.values("sport").annotate(v=Count("id")))
    hours={h:0 for h in range(6,24)}
    for row in qs.values("booking_time").annotate(v=Count("id")): hours[row["booking_time"].hour]=row["v"]
    goal=float(settings.monthly_revenue_goal or 1); goal_pct=min(float(month_r)/goal*100,100)
    most_dates=list(all_bookings.values("booking_date").annotate(total=Count("id")).order_by("-total", "-booking_date")[:5])
    avg_revenue=float(total_r/count) if count else 0
    return {"cards":cards,"today_revenue":today_r,"week_revenue":week_r,"month_revenue":month_r,"last_month_revenue":last_month_r,"total_revenue":total_r,"expenses_total":total_e,"net_income":net,
        "goal_pct":round(goal_pct,1),"goal":settings.monthly_revenue_goal,"occupancy":round(occupancy,1),"booked_hours":round(booked,1),"available_hours":round(available,1),
        "total_bookings":count,"today_bookings":today_count,"upcoming_bookings":confirmed,"completed_bookings":completed,"cancelled_bookings":cancelled,
        "completion_rate":round(completed/count*100,1) if count else 0,"average_revenue":round(avg_revenue,2),"most_booked_dates":most_dates,
        "charts":{"daily":{"labels":[d.strftime("%d %b") for d in days],"values":[float(daily_map.get(d,0)) for d in days]},
        "daily_bookings":{"labels":[d.strftime("%d %b") for d in days],"values":[daily_count_map.get(d,0) for d in days]},
        "monthly":{"labels":[x["period"].strftime("%b %Y") for x in monthly],"values":[float(x["v"]) for x in monthly]},
        "monthly_bookings":{"labels":[x["period"].strftime("%b %Y") for x in monthly_counts],"values":[x["v"] for x in monthly_counts]},
        "payment":{"labels":[x["payment_method"] for x in payment],"values":[x["v"] for x in payment]}, "sports":{"labels":[x["sport"] for x in sports],"values":[x["v"] for x in sports]},
        "hours":{"labels":[f"{h:02}:00" for h in hours],"values":list(hours.values())}}}


def ground_summaries(user):
    summaries = []
    for ground in Ground.objects.filter(owner=user, is_active=True):
        data = build_dashboard(user, ground)
        summaries.append({"ground": ground, **{key: data[key] for key in (
            "total_bookings", "today_bookings", "upcoming_bookings", "completed_bookings",
            "cancelled_bookings", "total_revenue", "today_revenue", "month_revenue", "occupancy")}})
    return summaries

def report_data(user,start,end):
    bookings=Booking.objects.filter(owner=user,booking_date__range=(start,end)).select_related("customer")
    expenses=Expense.objects.filter(owner=user,expense_date__range=(start,end)); revenue=total(bookings.exclude(status="Cancelled")); expense=total(expenses)
    return {"bookings":bookings,"expenses":expenses,"revenue":revenue,"expense_total":expense,"profit":revenue-expense,"start":start,"end":end}
