from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Product, Interaction, Review, GeneratedContent, Cart, CartItem, Order, OrderItem

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["age", "gender", "interests"]

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "profile"]

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, required=False, allow_null=True)
    class Meta:
        model = Product
        fields = ["id", "sku", "name", "description", "category", "price", "tags", "image_url", "image"]

class InteractionSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True, source="product")
    class Meta:
        model = Interaction
        fields = ["id", "user", "product", "product_id", "type", "rating", "created_at"]
        read_only_fields = ["id", "created_at"]

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "product", "user", "rating", "text", "created_at", "user_name"]
        read_only_fields = ["user"]

    def get_user_name(self, obj):
        return obj.user.get_username()

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["user"] = request.user
        return super().create(validated_data)

class GeneratedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedContent
        fields = ["ai_description", "reviews_summary", "updated_at"]

class ProductWithAIResolver(serializers.ModelSerializer):
    """
    Product serializer that includes cached AI fields if present.
    """
    generated = GeneratedContentSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "sku", "name", "description", "category", "price", "tags", "image_url", "generated"]

class LiteUserSerializer(serializers.ModelSerializer):
    interests = serializers.CharField(source="profile.interests", default="")
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "interests"]

class CartItemSerializer(serializers.ModelSerializer):
    product_detail = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ["id", "product", "qty", "product_detail"]

    def get_product_detail(self, obj):
        p = obj.product
        return {
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "image_url": p.image_url,
            "category": p.category
        }

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    class Meta:
        model = Cart
        fields = ["id", "is_active", "items"]

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "qty", "price"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ["id", "created_at", "total", "items"]