from __future__ import annotations

import re
from typing import Any, Sequence


def normalize_match_text(text: str) -> str:
    cleaned = str(text).lower().replace("'", "").replace("’", "")
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _catalog_details(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": product.get("id"),
        "name": product.get("name"),
        "brand": product.get("brand"),
        "sku": product.get("sku"),
        "barcode": product.get("barcode"),
    }


def match_product(
    ocr_texts: Sequence[str],
    catalog: Sequence[dict[str, Any]] | None,
    cutoff: float = 85.0,
    min_margin: float = 12.0,
) -> tuple[dict[str, Any] | None, float | None]:
    if not ocr_texts or not catalog:
        return None, None
    from rapidfuzz import fuzz

    queries = [normalize_match_text(text) for text in ocr_texts]
    joined = normalize_match_text(" ".join(ocr_texts))
    if joined:
        queries.append(joined)
    queries = list(dict.fromkeys(query for query in queries if query))
    if not queries:
        return None, None

    def code_key(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.lower())

    code_matches = []
    for product in catalog:
        if any(
            code_key(query) == code_key(code)
            for query in queries
            for code in (product.get("sku"), product.get("barcode"))
            if code and code_key(query)
        ):
            code_matches.append(product)
    if len(code_matches) == 1:
        return _catalog_details(code_matches[0]), 100.0
    if len(code_matches) > 1:
        return None, None

    exact_matches = []
    for product in catalog:
        if any(
            query == normalize_match_text(value)
            for query in queries
            for value in (product.get("name"), product.get("brand"))
            if value
        ):
            exact_matches.append(product)
    if len(exact_matches) == 1:
        return _catalog_details(exact_matches[0]), 100.0
    if len(exact_matches) > 1:
        return None, None

    queries = [query for query in queries if len(query.split()) >= 2]
    product_scores: list[tuple[dict[str, Any], float]] = []
    for product in catalog:
        variants = {
            normalize_match_text(value)
            for value in (
                product.get("name"),
                product.get("brand"),
                f"{product.get('brand') or ''} {product.get('name') or ''}",
            )
            if value
        }
        variants.discard("")
        if variants:
            score = max(
                fuzz.WRatio(query, variant)
                for query in queries
                for variant in variants
            )
            product_scores.append((product, float(score)))
    if not product_scores:
        return None, None
    product_scores.sort(key=lambda item: item[1], reverse=True)
    best_product, best_score = product_scores[0]
    if best_score < cutoff:
        return None, None
    if len(product_scores) > 1 and best_score - product_scores[1][1] < min_margin:
        return None, None
    return _catalog_details(best_product), round(best_score, 2)
