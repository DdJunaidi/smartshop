"""
AI helper functions:
- Prefer OpenAI for review summarization if OPENAI_API_KEY set.
- Otherwise use Gemini (Gemini also used for descriptions, search suggestions, chatbot).
"""

import os
import json
from typing import List, Dict
from django.utils import timezone

import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Optional OpenAI client (only if key is present)
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_KEY)
    except Exception:
        openai_client = None
else:
    openai_client = None

# ---------------- Gemini helpers ----------------

def gemini_generate_text(system: str, user: str, model: str = "gemini-flash-latest") -> str:
    """
    Single-turn text generation with Gemini.
    """
    g = genai.GenerativeModel(model)
    resp = g.generate_content([system, user])
    return (resp.text or "").strip()

def gemini_json(system: str, user: str, model: str = "gemini-flash-latest") -> Dict:
    """
    Ask Gemini for JSON. Be defensive about trailing text.
    """
    import re
    txt = gemini_generate_text(system, user, model)
    m = re.search(r"\{.*\}|\[.*\]", txt, flags=re.S)
    body = m.group(0) if m else "{}"
    try:
        return json.loads(body)
    except Exception:
        return {}

# ---------------- Feature-specific prompts ----------------

DESC_SYSTEM = (
    "You are an e-commerce copywriter. Write concise, engaging, factual "
    "product descriptions highlighting benefits, key specs, and use cases."
)

def generate_product_description(product) -> str:
    """
    Build a fresh AI description for a Product. Cached by the caller.
    """
    user = (
        f"Product:\n"
        f"- name: {product.name}\n"
        f"- category: {product.category}\n"
        f"- tags: {product.tags}\n"
        f"- base description: {product.description}\n\n"
        f"Write ~80-120 words, scannable, with short sentences."
    )
    return gemini_generate_text(DESC_SYSTEM, user)

SUMM_SYSTEM = (
    "You are an analytics assistant. Summarize product reviews with bullet points "
    "covering top pros and cons, overall sentiment (1 short line), and who it's best for."
)

def summarize_reviews_openai(review_texts: List[str]) -> str:
    """
    Use OpenAI (if configured) to summarize a list of reviews.
    """
    if not openai_client:
        return ""
    joined = "\n- ".join(r.strip() for r in review_texts if r.strip())
    prompt = (
        "Summarize the following customer reviews. Be concise; use bullet points.\n\n"
        f"Reviews:\n- {joined}"
    )
    resp = openai_client.responses.create(
        model="gpt-4o-mini",
        input=[{"role":"user","content":prompt}],
        temperature=0.2,
    )
    # Defensive extraction; adjust if SDK differs in your env.
    try:
        return resp.output_text.strip()
    except Exception:
        # Fallback parse
        return str(resp).strip()

def summarize_reviews(review_texts: List[str]) -> str:
    """
    Prefer OpenAI; fallback to Gemini if OPENAI_API_KEY is not set.
    """
    if openai_client:
        txt = summarize_reviews_openai(review_texts)
        if txt:
            return txt
    joined = "\n- ".join(r.strip() for r in review_texts if r.strip())
    return gemini_generate_text(SUMM_SYSTEM, f"Reviews:\n- {joined}\n\nSummarize as requested.")

# ---- Smart search helpers ----

SUGGEST_SYSTEM = (
    "You autocomplete short search queries for an e-commerce site. "
    "Return 5 short suggestions max, diverse but relevant. Output JSON array of strings."
)

def suggest_queries(q: str) -> List[str]:
    data = gemini_json(SUGGEST_SYSTEM, f"Query: {q}\nReturn JSON array only.")
    if isinstance(data, list):
        return [str(x)[:50] for x in data][:5]
    return []

CHAT_SYSTEM = (
    "You are a helpful shopping assistant on an e-commerce site. "
    "Answer concisely, ask clarifying questions if needed, and never invent product availability."
)

def chat_reply(message: str, context: str = "") -> str:
    user = f"User: {message}\n\nContext:\n{context}\n"
    return gemini_generate_text(CHAT_SYSTEM, user)
