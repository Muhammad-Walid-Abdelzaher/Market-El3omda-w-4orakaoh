import numpy as np

from computer_vision.temporal import compare_shelf_images


def detection(box, product_id=None, text=""):
    item = {
        "bbox": box,
        "label": text or "Unknown",
        "confidence": 0.9,
        "texts": [text] if text else [],
        "classification_status": "matched" if product_id is not None else "unknown",
    }
    if product_id is not None:
        item["matched_product"] = {"id": product_id, "name": text or f"Product {product_id}"}
    return item


def test_temporal_matches_changed_and_new():
    previous_image = np.zeros((100, 200, 3), dtype=np.uint8)
    current_image = previous_image.copy()
    previous = [
        detection([10, 10, 50, 50], 1, "Milk"),
        detection([80, 10, 120, 50], 2, "Cereal"),
    ]
    current = [
        detection([12, 12, 52, 52], 1, "Milk"),
        detection([140, 10, 180, 50], 3, "Coke"),
    ]
    result = compare_shelf_images(
        previous_image, current_image, previous, current
    )
    assert result["unchanged_count"] == 1
    assert result["disappeared_count"] == 1
    assert result["newly_visible_count"] == 1


def test_identical_product_at_distant_location_is_not_auto_matched():
    previous_image = np.zeros((100, 400, 3), dtype=np.uint8)
    current_image = previous_image.copy()
    previous = [detection([10, 10, 50, 50], 1, "Milk")]
    current = [detection([300, 10, 340, 50], 1, "Milk")]
    result = compare_shelf_images(
        previous_image, current_image, previous, current
    )
    assert result["unchanged_count"] == 0
    assert result["disappeared_count"] == 1
    assert result["newly_visible_count"] == 1
