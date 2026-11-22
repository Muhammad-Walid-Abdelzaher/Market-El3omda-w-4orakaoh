from computer_vision.product_matcher import match_product


def test_exact_catalog_match():
    catalog = [{
        "id": 101,
        "name": "Coca-Cola 330ml",
        "brand": "Coca-Cola",
        "sku": "CC330",
        "barcode": "123456789",
    }]
    matched, score = match_product(["CC330"], catalog)
    assert matched["id"] == 101
    assert score == 100.0


def test_ambiguous_brand_match_is_rejected():
    catalog = [
        {"id": 1, "name": "Coca-Cola 330ml", "brand": "Coca-Cola"},
        {"id": 2, "name": "Coca-Cola 500ml", "brand": "Coca-Cola"},
    ]
    assert match_product(["Coca-Cola"], catalog) == (None, None)
