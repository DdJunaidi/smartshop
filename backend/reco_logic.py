import os
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
from django.db.models import Count, Q
from django.contrib.auth.models import User
from .models import Product, Interaction
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ————————————————————————————————————————————————————————————————
# STEP A: Candidate generation (fast, rule-based, deterministic)
#  - Use signals (purchases, cart, views) to infer preferred categories/tags
#  - Pull popular items inside those categories/tags
# ————————————————————————————————————————————————————————————————

def generate_candidates_for_user(user: User, limit: int = 30) -> List[Product]:
    # 1) Get user's historical interactions
    user_interactions = Interaction.objects.filter(user=user).select_related("product")

    # 2) Score categories/tags by frequency and weight stronger signals higher
    weights = {"purchase": 5, "cart": 3, "rate": 2, "view": 1}
    cat_score = Counter()
    tag_score = Counter()

    for it in user_interactions:
        w = weights.get(it.type, 1)
        cat_score[it.product.category] += w
        for t in [s.strip().lower() for s in it.product.tags.split(",") if s.strip()]:
            tag_score[t] += w

    # If user is new (no signals), back off to overall popular products
    if not user_interactions.exists():
        popular = (Product.objects
                   .annotate(purchases=Count("interaction", filter=Q(interaction__type="purchase")))
                   .order_by("-purchases")[:limit])
        return list(popular)

    # 3) Pull products in top categories/tags, exclude things the user already purchased
    purchased_ids = set(Interaction.objects.filter(user=user, type="purchase").values_list("product_id", flat=True))
    top_cats = [c for c, _ in cat_score.most_common(5)]
    top_tags = [t for t, _ in tag_score.most_common(10)]

    # Q builds OR across categories and tags
    q = Q(category__in=top_cats)
    for t in top_tags:
        q |= Q(tags__icontains=t)

    candidates = (Product.objects
                  .filter(q)
                  .exclude(id__in=purchased_ids)
                  .annotate(pop=Count("interaction", filter=Q(interaction__type="purchase")))
                  .order_by("-pop")[:limit])

    return list(candidates)

# ————————————————————————————————————————————————————————————————
# STEP B: Gemini re-ranking with explanations
#  - Prompt Gemini to score each candidate 0..1 and provide a short reason
#  - Return scores + reasons to front-end (explainability "why recommended")
# ————————————————————————————————————————————————————————————————

RERANK_PROMPT_TMPL = """
You are a recommender system assistant.
Given a user profile and a list of candidate products (with category,tags), return a JSON array where each item is:
{{"sku": "<sku>", "score": <0..1>, "reason": "<<= 15 words concise reason>"}}

User:
- age: {age}
- gender: {gender}
- interests: {interests}

Recent signals (most important first):
{signals}

Candidates:
{candidates}

Guidelines:
- Prefer products that match interests, recent actions, and tag overlap.
- Keep "reason" < 15 words, specific (mention a tag or category if relevant).
- Output ONLY valid JSON array. No backticks, no extra text.
"""

def strip_json(text: str) -> str:
    """
    Be defensive: models sometimes wrap JSON. Extract the first JSON array.
    """
    m = re.search(r"\[.*\]", text, flags=re.S)
    return m.group(0) if m else "[]"

def rerank_with_gemini(user: User, candidates: List[Product]) -> List[Dict[str, Any]]:
    # Profile summary
    profile = getattr(user, "profile", None)
    age = getattr(profile, "age", None) or "unknown"
    gender = getattr(profile, "gender", None) or "unknown"
    interests = getattr(profile, "interests", "") or "unknown"

    # Recent interactions (for recency) — most recent 20
    recents = (Interaction.objects
               .filter(user=user)
               .select_related("product")
               .order_by("-created_at")[:20])

    # Format signals and candidates for the LLM
    signals_fmt = "\n".join(
        f"- {i.type} • {i.product.name} • {i.product.category} • tags={i.product.tags}" for i in recents
    )
    candidates_fmt = "\n".join(
        f"- sku={p.sku} | name={p.name} | category={p.category} | tags={p.tags}" for p in candidates
    )

    prompt = RERANK_PROMPT_TMPL.format(
        age=age, gender=gender, interests=interests,
        signals=signals_fmt or "none",
        candidates=candidates_fmt or "none"
    )

    model = genai.GenerativeModel("gemini-flash-latest")  
    resp = model.generate_content(prompt)
    json_text = strip_json(resp.text or "[]")

    # Parse safely
    import json
    try:
        data = json.loads(json_text)
        # Filter to known SKUs only, add product object
        by_sku = {p.sku: p for p in candidates}
        results = []
        for item in data:
            sku = item.get("sku")
            if sku in by_sku:
                results.append({
                    "sku": sku,
                    "score": float(item.get("score", 0)),
                    "reason": item.get("reason", "Recommended"),
                    "product": by_sku[sku],
                })
        # Sort by descending score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    except Exception:
        # Fallback: if model returned junk, return top candidates with generic reasons
        return [{"sku": p.sku, "score": 0.5, "reason": "Popular in your interests", "product": p}
                for p in candidates]
