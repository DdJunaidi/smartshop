import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from backend.models import Profile, Product, Interaction

class Command(BaseCommand):
    help = "Seed demo users, products, and a bit of interactions"

    def handle(self, *args, **kwargs):
        # Products
        with open("backend/fixtures/products.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                Product.objects.update_or_create(
                    sku=row["sku"],
                    defaults={
                        "name": row["name"],
                        "description": row["description"],
                        "category": row["category"],
                        "price": row["price"],
                        "tags": row.get("tags", ""),
                        "image_url": row.get("image_url", ""),
                    }
                )

        # Users + profiles
        with open("backend/fixtures/users.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                user, _ = User.objects.get_or_create(
                    username=row["username"],
                    defaults={
                        "first_name": row["first_name"],
                        "last_name": row["last_name"],
                        "email": row["email"],
                    }
                )
                user.set_password("password123")
                user.save()
                Profile.objects.update_or_create(
                    user=user,
                    defaults={
                        "age": int(row["age"]),
                        "gender": row["gender"],
                        "interests": row["interests"],
                    }
                )

        # A few interactions to make recommendations meaningful
        alice = User.objects.get(username="alice")
        bob = User.objects.get(username="bob")
        hp = Product.objects.get(sku="ELEC-100")
        eb = Product.objects.get(sku="ELEC-101")
        shoe = Product.objects.get(sku="SPORT-200")
        coffee = Product.objects.get(sku="HOME-400")
        book = Product.objects.get(sku="BOOK-300")

        Interaction.objects.get_or_create(user=alice, product=hp, type="view")
        Interaction.objects.get_or_create(user=alice, product=eb, type="purchase", rating=5)
        Interaction.objects.get_or_create(user=alice, product=shoe, type="view")

        Interaction.objects.get_or_create(user=bob, product=coffee, type="purchase", rating=4)
        Interaction.objects.get_or_create(user=bob, product=book, type="view")

        self.stdout.write(self.style.SUCCESS("Seeded products, users, interactions."))
