from __future__ import annotations

import colorsys
from typing import Any, Sequence

import cv2
import numpy as np


def _class_color(class_id: int) -> tuple[int, int, int]:
    hue = (class_id * 0.618033988749895) % 1.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.78, 0.98)
    return round(blue * 255), round(green * 255), round(red * 255)


def _draw_label(
    image: np.ndarray,
    text: str,
    origin: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    thickness = 1
    (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
    label_width = text_width + 26
    if label_width > image.shape[1]:
        text = text[: max(1, int(len(text) * image.shape[1] / label_width) - 3)] + "..."
        (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
        label_width = min(image.shape[1], text_width + 26)
    x, y = origin
    x = max(0, min(x, image.shape[1] - label_width))
    baseline_y = max(text_height + 8, min(y, image.shape[0] - baseline - 1))
    top = max(0, baseline_y - text_height - 8)
    bottom = min(image.shape[0] - 1, baseline_y + baseline + 4)
    right = min(image.shape[1] - 1, x + label_width)
    cv2.rectangle(image, (x, top), (right, bottom), (24, 30, 43), cv2.FILLED)
    cv2.line(image, (x + 4, top), (x + 4, bottom), color, 3)
    cv2.putText(
        image,
        text,
        (x + 11, baseline_y - 3),
        font,
        scale,
        (245, 248, 252),
        thickness,
    )


def annotate_image(
    image: np.ndarray,
    detections: Sequence[dict[str, Any]],
) -> np.ndarray:
    annotated = image.copy()
    for detection in detections:
        box = detection.get("bbox")
        if not isinstance(box, (list, tuple, np.ndarray)) or len(box) != 4:
            continue
        x1, y1, x2, y2 = [int(round(float(value))) for value in box]
        matched_product = detection.get("matched_product")
        color_id = (
            100_000 + int(matched_product["id"])
            if matched_product and matched_product.get("id") is not None
            else int(detection.get("class_id", 0))
        )
        color = _class_color(color_id)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (24, 30, 43), 4)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        display_label = (
            str(detection["label"])
            if matched_product
            else f"Unknown: {detection.get('label', 'Unknown')}"
        )
        confidence = detection.get("confidence")
        label_text = (
            f"{display_label} {float(confidence):.2f}"
            if confidence is not None
            else display_label
        )
        _draw_label(annotated, label_text, (x1, max(18, y1 - 5)), color)
    return annotated
