import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from backend.models import Product, Interaction

@pytest.mark.django_db
def test_recommendations_endpoint_happy_path(monkeypatch):
    # Arrange
    u = User.objects.create_user("alice", password="x")
    p = Product.objects.create(sku="E1", name="Earbuds", category="Electronics",
                               price=99, tags="earbuds,audio")
    Interaction.objects.create(user=u, product=p, type="view")

    # Stub rerank_with_gemini to avoid external API
    def fake_rerank_with_gemini(user, candidates):
        # simulate a minimal rerank result structure
        return [{"product": p, "score": 0.99, "reason": "Recent views on audio gear."}]
    # IMPORTANT: patch the symbol where it's used (in backend.views)
    from backend import views
    monkeypatch.setattr(views, "rerank_with_gemini", fake_rerank_with_gemini)

    # Act
    c = APIClient()
    r = c.get(f"/api/recommendations/{u.id}/")

    # Assert
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert body and body[0]["name"] == "Earbuds"
    assert "reason" in body[0] and "score" in body[0]
