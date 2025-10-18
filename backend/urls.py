from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ProductViewSet, InteractionViewSet, ReviewViewSet,
    cart_detail, cart_add, cart_update, checkout,
    RecommendForUser, DemoUsers, search_products, search_suggest,
    generate_description, summarize_product_reviews, chatbot_reply, Me, RecommendForMe,
)
from .views_auth import IssueToken  # <-- our logging token view

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"interactions", InteractionViewSet, basename="interaction")
router.register(r"reviews", ReviewViewSet, basename="review")

urlpatterns = [
    # DRF viewsets
    path("", include(router.urls)),

    # Recos & search
    path("recommendations/<int:user_id>/", RecommendForUser.as_view()),
    path("recommendations/me/", RecommendForMe.as_view()),
    path("demo-users/", DemoUsers.as_view()),
    path("search", search_products),
    path("search/suggest", search_suggest),

    # AI content
    path("products/<int:product_id>/generate_description", generate_description),
    path("products/<int:product_id>/summarize_reviews", summarize_product_reviews),

    # Chatbot
    path("chatbot/", chatbot_reply),

    # Me
    path("me/", Me.as_view()),

    # Cart & checkout
    path("cart/", cart_detail),
    path("cart/add", cart_add),
    path("cart/update", cart_update),
    path("checkout/", checkout),

    # JWT with login logging
    path("token/", IssueToken.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
