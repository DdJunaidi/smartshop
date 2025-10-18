import pytest
from backend.models import Product

@pytest.mark.django_db
def test_search_endpoint_returns_expected(client):
    Product.objects.create(
        sku="SB1", name="SoundBar Mini",
        category="Electronics", price=99, tags="soundbar,tv"
    )

    # Current endpoint uses __icontains on the WHOLE query string (no tokenization),
    # so "soundbar" will match, but "sound bar" may not.
    r = client.get("/api/search", {"q": "soundbar"})
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    names = [p["name"] for p in body["results"]]
    assert any("SoundBar" in n for n in names), f"Expected 'SoundBar' result, got {names}"
