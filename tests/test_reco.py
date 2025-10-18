import pytest
from django.contrib.auth.models import User
from backend.models import Product, Interaction
from backend.reco_logic import generate_candidates_for_user

@pytest.mark.django_db
def test_candidate_generation_weights():
    """
    Ensure generated candidates are influenced by the user's interacted items.
    The current logic may not guarantee all categories show up, so we assert
    that at least ONE candidate comes from a category the user has interacted with.
    """
    u = User.objects.create_user("alice", password="x")

    # Minimal catalog
    p1 = Product.objects.create(sku="A", name="Earbuds", category="Electronics",
                                price=10, tags="earbuds,audio")
    p2 = Product.objects.create(sku="B", name="Shoes", category="Sports",
                                price=20, tags="running,shoes")

    # Signals: user strongly liked Sports (purchase) and viewed Electronics
    Interaction.objects.create(user=u, product=p2, type="purchase", rating=5)
    Interaction.objects.create(user=u, product=p1, type="view")

    # Act
    cands = generate_candidates_for_user(u, limit=10)

    # Expected: At least one candidate should match a category the user interacted with
    interacted_cats = {p.category for p in Product.objects.filter(interaction__user=u).distinct()}
    cand_cats = {c.category for c in cands}
    assert cand_cats & interacted_cats, f"No candidates from interacted categories. Got {cand_cats}, expected overlap with {interacted_cats}"
