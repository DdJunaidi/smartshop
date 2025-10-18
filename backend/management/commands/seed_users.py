# backend/management/commands/seed_users.py
import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

FIXTURE = Path(__file__).resolve().parent.parent.parent / "fixtures" / "users.csv"

class Command(BaseCommand):
    help = "Seed users from fixtures/users.csv (with password column)."

    def handle(self, *args, **opts):
        with open(FIXTURE, newline="", encoding="utf-8") as f:
            for i, row in enumerate(csv.DictReader(f), start=1):
                u, created = User.objects.get_or_create(
                    username=row["username"],
                    defaults=dict(
                        first_name=row.get("first_name",""),
                        last_name=row.get("last_name",""),
                        email=row.get("email",""),
                    )
                )
                pwd = row.get("password") or "SmartShop#123"
                u.set_password(pwd)
                u.save()
                self.stdout.write(f"[{i}] {'CREATED' if created else 'UPDATED'} {u.username}")
        self.stdout.write(self.style.SUCCESS("Done."))
