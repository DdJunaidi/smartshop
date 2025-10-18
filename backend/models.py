from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """
    Lightweight user profile to capture preferences we can feed into the model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    # comma-separated interests: "electronics, audio, running"
    interests = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Profile({self.user.username})"

class Product(models.Model):
    """
    Product catalog with tags for simple content-based similarity.
    """
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # comma-separated tags: "headphones, bluetooth, sport, sony"
    tags = models.TextField(blank=True, default="")
    image_url = models.URLField(blank=True, default="")
    image = models.ImageField(upload_to="products/", null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.category})"

class Interaction(models.Model):
    """
    Captures user signals we can use for candidate generation.
    type: 'view' | 'cart' | 'purchase' | 'rate'
    rating: optional 1-5 when type == 'rate'
    """
    VIEW = "view"; CART = "cart"; PURCHASE = "purchase"; RATE = "rate"
    TYPES = [(VIEW, "View"), (CART, "AddToCart"), (PURCHASE, "Purchase"), (RATE, "Rate")]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    type = models.CharField(max_length=16, choices=TYPES)
    rating = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "type", "created_at"])]

    def __str__(self):
        return f"{self.user.username} {self.type} {self.product.sku}"

class Review(models.Model):
    """
    Simple user review model used for summarization demos.
    In real apps you'd tie to orders, moderation, etc.
    """
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)  # 1..5
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["product", "created_at"])]

    def __str__(self):
        return f"Review({self.product.sku}, {self.rating}★)"

class GeneratedContent(models.Model):
    """
    Cache AI-generated content for a product so we don't pay the LLM every time.
    """
    product = models.OneToOneField("Product", on_delete=models.CASCADE, related_name="generated")
    ai_description = models.TextField(blank=True, default="")
    reviews_summary = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GeneratedContent({self.product.sku})"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")
    is_active = models.BooleanField(default=True)  # one active cart per user
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart({self.user.username}) active={self.is_active}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("Product", on_delete=models.PROTECT)
    qty = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot

class LoginEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} @ {self.created_at:%Y-%m-%d %H:%M}"

