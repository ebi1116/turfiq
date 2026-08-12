import random
from datetime import time, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Booking, Customer
from business.models import BusinessSettings, Ground
from expenses.models import Expense

class Command(BaseCommand):
    help = "Create a demo owner and realistic sample analytics data."
    def handle(self, *args, **options):
        random.seed(42); user, created = User.objects.get_or_create(username="demo", defaults={"first_name":"Alex","last_name":"Morgan","email":"demo@turfiq.local"})
        if created: user.set_password("Demo@12345"); user.save()
        turf, _ = BusinessSettings.objects.update_or_create(owner=user, defaults={"business_name":"Greenfield Arena","monthly_revenue_goal":Decimal("180000"), "number_of_grounds": 3})
        grounds = [Ground.objects.get_or_create(owner=user, turf=turf, number=number, defaults={"name": name})[0] for number, name in enumerate(("Arena A", "Arena B", "Indoor Court"), 1)]
        names=[("Arjun Nair","9876500011"),("Rohan Shah","9876500012"),("Neha Kapoor","9876500013"),("Kabir Mehta","9876500014"),("Priya Das","9876500015"),("Vikram Rao","9876500016")]
        customers=[Customer.objects.get_or_create(owner=user,phone=p,defaults={"name":n})[0] for n,p in names]
        today=timezone.localdate(); sports=["Football","Cricket","Badminton","Other"]; payments=["UPI","Cash","Card","Online"]
        if not Booking.objects.filter(owner=user).exists():
            for i in range(120):
                date=today-timedelta(days=random.randint(0,180)); hour=random.choice(range(6,23)); status=random.choices(["Completed","Confirmed","Cancelled","Pending"],[60,25,8,7])[0]
                Booking.objects.create(owner=user,customer=random.choice(customers),booking_date=date,booking_time=time(hour,0),duration=Decimal(str(random.choice([1,1.5,2]))),sport=random.choice(sports),ground=random.choice(grounds),amount=Decimal(random.choice([800,1000,1200,1500,1800,2200])),payment_method=random.choice(payments),status=status,is_paid=status!="Pending")
        if not Expense.objects.filter(owner=user).exists():
            for i in range(28): Expense.objects.create(owner=user,category=random.choice([x[0] for x in Expense.CATEGORIES]),amount=Decimal(random.choice([500,1200,2500,5000,12000])),expense_date=today-timedelta(days=random.randint(0,180)))
        self.stdout.write(self.style.SUCCESS("Demo ready: username demo / password Demo@12345"))
