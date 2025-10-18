from django.contrib import admin
from .models import Product, Interaction, Profile, Review, GeneratedContent, LoginEvent

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "price")
    search_fields = ("sku", "name", "category", "tags")
    list_filter = ("category",)
    ordering = ("category", "name")

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "type", "rating", "created_at")
    list_filter = ("type", "created_at")
    search_fields = ("user__username", "product__name", "product__sku")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "gender", "interests")
    search_fields = ("user__username", "interests")

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "rating", "user", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "text")

@admin.register(GeneratedContent)
class GeneratedContentAdmin(admin.ModelAdmin):
    list_display = ("product", "updated_at")
    search_fields = ("product__name",)

@admin.register(LoginEvent)
class LoginEventAdmin(admin.ModelAdmin):
    list_display = ("user", "ip", "created_at")
    search_fields = ("user__username", "ip", "user_agent")
    list_filter = ("created_at",)