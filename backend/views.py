import os
import google.generativeai as genai
from django.db.models import Q, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import Product, Interaction, GeneratedContent, Review, Cart, CartItem, Order, OrderItem
from .ai_clients import generate_product_description, summarize_reviews, chat_reply, suggest_queries
from .serializers import ProductSerializer, InteractionSerializer, ProductWithAIResolver, ReviewSerializer, LiteUserSerializer, CartSerializer, OrderSerializer
from .reco_logic import generate_candidates_for_user, rerank_with_gemini
from django.db import transaction
from decimal import Decimal

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/products/ (list)
    GET /api/products/:id/ (detail)
    """
    queryset = Product.objects.all().order_by("name")
    serializer_class = ProductSerializer

class InteractionViewSet(viewsets.ModelViewSet):
    """
    POST /api/interactions/   (requires JWT)
    GET  /api/interactions/   (requires JWT; filterable by ?user=)
    """
    queryset = Interaction.objects.all().order_by("-created_at").select_related("product", "user")
    serializer_class = InteractionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional filter
        user_id = self.request.query_params.get("user")
        if user_id:
            qs = qs.filter(user_id=user_id)
        else:
            # default: show current user's interactions
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        # always attach the current user; clients must NOT send 'user'
        serializer.save(user=self.request.user)

class RecommendForUser(APIView):
    """
    GET /api/recommendations/<user_id>/
    Returns: [{ product: {..}, score: float, reason: str }, ...]
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # ---- 1) Fast mode toggle (skip Gemini) ----
        fast = request.query_params.get("fast") in ("1", "true", "yes")

        # ---- 2) Cache key per-user & mode ----
        cache_key = f"recs:{user.id}:{'fast' if fast else 'full'}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached, status=200)

        # ---- 3) Generate candidates quickly ----
        candidates = generate_candidates_for_user(user, limit=30)

        if fast:
            # No LLM rerank — just take top-N heuristic candidates
            products = [
                {
                    **ProductSerializer(p, context={"request": request}).data,
                    "score": 0.0,
                    "reason": "Heuristic match",
                }
                for p in candidates[:10]
            ]
        else:
            # Full rerank with Gemini
            ranked = rerank_with_gemini(user, candidates)[:10]
            products = []
            for r in ranked:
                p = r["product"]
                pdata = ProductSerializer(p, context={"request": request}).data
                products.append({
                    **pdata,
                    "score": r["score"],
                    "reason": r["reason"],
                })

        # ---- 4) Cache for a short time (e.g., 2 minutes) ----
        cache.set(cache_key, products, timeout=120)
        return Response(products, status=200)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

class DemoUsers(APIView):
    """GET /api/demo-users/ — list non-superusers for the dropdown."""
    def get(self, request):
        qs = User.objects.filter(is_superuser=False).order_by("username")
        return Response(LiteUserSerializer(qs, many=True).data)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().order_by("-created_at")
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        pid = self.request.query_params.get("product")
        if pid:
            qs = qs.filter(product_id=pid)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class Me(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        # include profile interests if you have it
        interests = getattr(getattr(u, "profile", None), "interests", "")
        return Response({
            "id": u.id, "username": u.username, "email": u.email,
            "first_name": u.first_name, "last_name": u.last_name,
            "interests": interests
        })

class RecommendForMe(APIView):
    """
    GET /api/recommendations/me/  (JWT required)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # ---- 1) Fast mode toggle (skip Gemini) ----
        fast = request.query_params.get("fast") in ("1", "true", "yes")

        # ---- 2) Cache key per-user & mode ----
        cache_key = f"recs:{user.id}:{'fast' if fast else 'full'}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached, status=200)

        # ---- 3) Generate candidates quickly ----
        candidates = generate_candidates_for_user(user, limit=30)

        if fast:
            # No LLM rerank — just take top-N heuristic candidates
            products = [
                {
                    **ProductSerializer(p, context={"request": request}).data,
                    "score": 0.0,
                    "reason": "Heuristic match",
                }
                for p in candidates[:10]
            ]
        else:
            # Full rerank with Gemini
            ranked = rerank_with_gemini(user, candidates)[:10]
            products = []
            for r in ranked:
                p = r["product"]
                pdata = ProductSerializer(p, context={"request": request}).data
                products.append({
                    **pdata,
                    "score": r["score"],
                    "reason": r["reason"],
                })

        # ---- 4) Cache for a short time (e.g., 2 minutes) ----
        cache.set(cache_key, products, timeout=120)
        return Response(products, status=200)


@api_view(["GET"])
def search_products(request):
    """
    GET /api/search?q=running headphones
    - basic lexical match over name/description/tags/category
    - can be extended to vector/semantic retrieval
    """
    q = (request.GET.get("q") or "").strip()
    base = Product.objects.all()
    if q:
        # very simple scoring via ORs; you can swap with a vector index later
        base = base.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(tags__icontains=q) |
            Q(category__icontains=q)
        )
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(base.order_by("name"), request)
    ser = ProductWithAIResolver(page, many=True)
    return paginator.get_paginated_response(ser.data)

@api_view(["GET"])
def search_suggest(request):
    """
    GET /api/search/suggest?q=hea
    Returns simple LLM-based suggestions.
    """
    q = (request.GET.get("q") or "").strip()
    if not q:
        return Response([], status=200)
    return Response(suggest_queries(q) or [], status=200)

@api_view(["POST"])
def generate_description(request, product_id: int):
    """
    POST /api/products/<id>/generate_description
    - generates & caches an AI description for the product
    """
    try:
        p = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)

    text = generate_product_description(p)
    gc, _ = GeneratedContent.objects.get_or_create(product=p)
    gc.ai_description = text
    gc.save(update_fields=["ai_description", "updated_at"])
    return Response({"ai_description": text}, status=200)

@api_view(["POST"])
def summarize_product_reviews(request, product_id: int):
    """
    POST /api/products/<id>/summarize_reviews
    - summarizes existing Review rows; caches to GeneratedContent
    """
    try:
        p = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)

    reviews = list(p.reviews.order_by("-created_at").values_list("text", flat=True)[:50])
    if not reviews:
        return Response({"reviews_summary": "No reviews yet."}, status=200)

    summary = summarize_reviews(reviews)
    gc, _ = GeneratedContent.objects.get_or_create(product=p)
    gc.reviews_summary = summary
    gc.save(update_fields=["reviews_summary", "updated_at"])
    return Response({"reviews_summary": summary}, status=200)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

SYSTEM_PROMPT = (
    "You are SmartShop, a helpful shopping assistant for an e-commerce site. "
    "Answer concisely about products, categories, prices, availability (if known), "
    "and general shopping questions. If you don't know, say so briefly."
)

def _normalize_history_for_gemini(history):
    """
    Frontend sends: [{"role":"user","text":"..."}, {"role":"assistant","text":"..."}]
    Gemini expects 'user' and 'model' roles + parts.
    """
    mapped = []
    for m in history or []:
        text = (m.get("text") or "").strip()
        if not text:
            continue
        role = "user" if m.get("role") == "user" else "model"
        mapped.append({"role": role, "parts": [text]})
    return mapped

@api_view(["POST"])
@permission_classes([AllowAny])  # keep public for demo; switch to IsAuthenticated in production
def chatbot_reply(request):
    """
    POST /api/chatbot/

    Two input shapes are supported:

    A) Multi-turn (recommended by the UI widget):
       body: {"history": [{"role":"user","text":"..."},{"role":"assistant","text":"..."}]}

    B) Single message (legacy):
       body: {"message": "Do you have sport earbuds?"}

    Response (both cases):
       {"reply": {"role":"assistant","text":"..."}}
    """
    if not os.environ.get("GEMINI_API_KEY"):
        return Response({"reply": {"role": "assistant", "text": "Gemini API key is not configured."}}, status=200)

    # Small product context (top items by interaction count)
    top = Product.objects.annotate(pop=Count("interaction")).order_by("-pop")[:10]
    ctx = "\n".join([f"- {p.name} ({p.category}) tags={p.tags}" for p in top])

    # Prefer multi-turn when 'history' is provided
    history = request.data.get("history")
    if isinstance(history, list) and history:
        # Trim to control token usage (keep last N user/assistant messages)
        MAX_TURNS = 10
        history = history[-(2 * MAX_TURNS):]

        contents = _normalize_history_for_gemini(history)

        try:
            model = genai.GenerativeModel(
                model_name="gemini-flash-latest",
                system_instruction=SYSTEM_PROMPT + "\n\nContext:\n" + ctx,
            )
            resp = model.generate_content(
                contents,
                generation_config={"temperature": 0.6, "top_p": 0.9, "max_output_tokens": 512},
            )
            text = (resp.text or "").strip() or "I couldn't generate a response right now."
            return Response({"reply": {"role": "assistant", "text": text}}, status=200)
        except Exception:
            return Response({"reply": {"role": "assistant", "text": "Sorry, I ran into an error."}}, status=200)

    # Fallback: single-turn message (legacy)
    msg = (request.data or {}).get("message", "").strip()
    if not msg:
        return Response({"reply": {"role": "assistant", "text": "Please type a question."}}, status=200)

    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=SYSTEM_PROMPT + "\n\nContext:\n" + ctx,
        )
        resp = model.generate_content(
            [{"role": "user", "parts": [msg]}],
            generation_config={"temperature": 0.6, "top_p": 0.9, "max_output_tokens": 512},
        )
        text = (resp.text or "").strip() or "I couldn't generate a response right now."
        return Response({"reply": {"role": "assistant", "text": text}}, status=200)
    except Exception:
        return Response({"reply": {"role": "assistant", "text": "Sorry, I ran into an error."}}, status=200)


def get_or_create_active_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user, is_active=True)
    return cart

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    cart = get_or_create_active_cart(request.user)
    return Response(CartSerializer(cart).data, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cart_add(request):
    """
    body: { "product_id": <int>, "qty": <int> }
    """
    pid = int(request.data.get("product_id"))
    qty = int(request.data.get("qty") or 1)
    if qty < 1:
        qty = 1
    try:
        p = Product.objects.get(pk=pid)
    except Product.DoesNotExist:
        return Response({"detail": "Product not found"}, status=404)

    cart = get_or_create_active_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=p)
    if created:
        item.qty = qty
    else:
        item.qty += qty
    item.save()
    return Response(CartSerializer(cart).data, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cart_update(request):
    """
    body: { "item_id": <int>, "qty": <int> }
    """
    item_id = int(request.data.get("item_id"))
    qty = int(request.data.get("qty") or 1)
    try:
        item = CartItem.objects.get(pk=item_id, cart__user=request.user, cart__is_active=True)
    except CartItem.DoesNotExist:
        return Response({"detail": "Item not found"}, status=404)

    if qty <= 0:
        item.delete()
    else:
        item.qty = qty
        item.save()
    cart = item.cart if item.id else get_or_create_active_cart(request.user)
    return Response(CartSerializer(cart).data, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def checkout(request):
    """
    Creates an Order from the active cart and clears it.
    """
    cart = get_or_create_active_cart(request.user)
    if not cart.items.exists():
        return Response({"detail": "Cart is empty."}, status=400)

    order = Order.objects.create(user=request.user, total=Decimal("0.00"))
    total = Decimal("0.00")
    for it in cart.items.select_related("product"):
        price = it.product.price
        OrderItem.objects.create(order=order, product=it.product, qty=it.qty, price=price)
        total += (price * it.qty)
    order.total = total
    order.save()

    # close cart
    cart.is_active = False
    cart.save(update_fields=["is_active"])
    cart.items.all().delete()

    return Response(OrderSerializer(order).data, status=201)

