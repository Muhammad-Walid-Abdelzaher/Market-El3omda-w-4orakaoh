from __future__ import annotations

from typing import Any, Sequence

import cv2
import numpy as np

from .config import ComputerVisionConfig
from .product_matcher import normalize_match_text


def _valid_bbox(box: Any) -> bool:
    if not isinstance(box, (list, tuple, np.ndarray)) or len(box) != 4:
        return False
    try:
        values = [float(value) for value in box]
    except (TypeError, ValueError):
        return False
    return (
        all(np.isfinite(value) for value in values)
        and values[0] >= 0
        and values[1] >= 0
        and values[2] > values[0]
        and values[3] > values[1]
    )


def calculate_iou(a: Sequence[float], b: Sequence[float]) -> float:
    if not _valid_bbox(a) or not _valid_bbox(b):
        return 0.0
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    iw = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    ih = max(0.0, min(ay2, by2) - max(ay1, by1))
    intersection = iw * ih
    area_a = max(1.0, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1.0, (bx2 - bx1) * (by2 - by1))
    return float(intersection / (area_a + area_b - intersection))


def calculate_center_distance(
    a: Sequence[float],
    b: Sequence[float],
    width: int,
    height: int,
) -> float:
    if not _valid_bbox(a) or not _valid_bbox(b):
        return float("inf")
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    ca = np.array([(ax1 + ax2) / 2, (ay1 + ay2) / 2])
    cb = np.array([(bx1 + bx2) / 2, (by1 + by2) / 2])
    diagonal = max(1.0, float(np.hypot(width, height)))
    return float(np.linalg.norm(ca - cb) / diagonal)


def _estimate_homography(
    previous_image: np.ndarray,
    current_image: np.ndarray,
    config: ComputerVisionConfig,
) -> tuple[Any | None, dict[str, Any]]:
    if previous_image is None or current_image is None:
        return None, {"status": "invalid_images", "inlier_ratio": None}
    gray_previous = cv2.cvtColor(previous_image, cv2.COLOR_BGR2GRAY)
    gray_current = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)
    detector = cv2.ORB_create(nfeatures=1200)
    kp_previous, desc_previous = detector.detectAndCompute(gray_previous, None)
    kp_current, desc_current = detector.detectAndCompute(gray_current, None)
    if desc_previous is None or desc_current is None:
        return None, {"status": "insufficient_features", "inlier_ratio": None}
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(
        desc_previous, desc_current
    )
    matches = sorted(matches, key=lambda match: match.distance)[:300]
    if len(matches) < config.homography_min_matches:
        return None, {"status": "insufficient_matches", "inlier_ratio": None}
    points_previous = np.float32(
        [kp_previous[match.queryIdx].pt for match in matches]
    ).reshape(-1, 1, 2)
    points_current = np.float32(
        [kp_current[match.trainIdx].pt for match in matches]
    ).reshape(-1, 1, 2)
    homography, mask = cv2.findHomography(
        points_previous,
        points_current,
        method=cv2.RANSAC,
        ransacReprojThreshold=config.homography_ransac_threshold,
    )
    if homography is None or mask is None:
        return None, {"status": "homography_failed", "inlier_ratio": None}
    inlier_ratio = float(mask.ravel().sum()) / float(len(mask))
    if inlier_ratio < config.homography_max_match_inliers_ratio:
        return None, {
            "status": "low_inlier_ratio",
            "inlier_ratio": round(inlier_ratio, 4),
        }
    return homography, {
        "status": "aligned",
        "inlier_ratio": round(inlier_ratio, 4),
        "match_count": len(matches),
    }


def _normalized_detection_text(detection: dict[str, Any]) -> str:
    product = detection.get("matched_product")
    values = (
        [product.get("name"), product.get("brand"), *detection.get("texts", [])]
        if product
        else detection.get("texts", [])
    )
    normalized = [normalize_match_text(str(value)) for value in values if value]
    return " ".join(normalized)


def _text_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    previous = _normalized_detection_text(a)
    current = _normalized_detection_text(b)
    if not previous or not current:
        return 0.0
    try:
        from rapidfuzz import fuzz
        return float(fuzz.WRatio(previous, current) / 100.0)
    except ImportError:
        return 1.0 if previous == current else 0.0


def calculate_text_similarity(
    previous_detection: dict[str, Any],
    current_detection: dict[str, Any],
) -> float:
    """Public wrapper for normalized OCR/catalog text similarity."""
    return _text_similarity(previous_detection, current_detection)


def calculate_appearance_similarity(
    previous_image: np.ndarray,
    previous_box: Sequence[float],
    current_image: np.ndarray,
    current_box: Sequence[float],
) -> float:
    """Compare HSV crop histograms for a pair of detections."""
    if not _valid_bbox(previous_box) or not _valid_bbox(current_box):
        return 0.0

    def histogram(image: np.ndarray, box: Sequence[float]) -> np.ndarray | None:
        height, width = image.shape[:2]
        x1, y1, x2, y2 = (int(round(float(value))) for value in box)
        x1, x2 = max(0, min(width, x1)), max(0, min(width, x2))
        y1, y2 = max(0, min(height, y1)), max(0, min(height, y2))
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        return hist

    previous_hist = histogram(previous_image, previous_box)
    current_hist = histogram(current_image, current_box)
    if previous_hist is None or current_hist is None:
        return 0.0
    return float(
        max(
            0.0,
            cv2.compareHist(
                previous_hist,
                current_hist,
                cv2.HISTCMP_CORREL,
            ),
        )
    )


def _transform_box(
    detection: dict[str, Any],
    homography: Any,
    current_shape: tuple[int, int],
) -> list[float]:
    box = detection.get("bbox")
    if not _valid_bbox(box):
        return []
    x1, y1, x2, y2 = map(float, box)
    if homography is None:
        return [x1, y1, x2, y2]
    corners = np.array([[[x1, y1], [x2, y1], [x2, y2], [x1, y2]]], dtype=np.float32)
    transformed = cv2.perspectiveTransform(corners, homography)[0]
    height, width = current_shape
    xs = np.clip(transformed[:, 0], 0, width)
    ys = np.clip(transformed[:, 1], 0, height)
    return [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]


def compare_shelf_images(
    previous_image: np.ndarray,
    current_image: np.ndarray,
    previous_detections: list[dict[str, Any]],
    current_detections: list[dict[str, Any]],
    config: ComputerVisionConfig | None = None,
) -> dict[str, Any]:
    config = config or ComputerVisionConfig()
    if not isinstance(previous_image, np.ndarray) or not isinstance(current_image, np.ndarray):
        raise ValueError("Previous and current images must be valid NumPy arrays.")

    homography, alignment = _estimate_homography(
        previous_image, current_image, config
    )
    alignment_available = homography is not None
    previous_boxes = [
        _transform_box(detection, homography, current_image.shape[:2])
        for detection in previous_detections
    ]
    previous_count = len(previous_detections)
    current_count = len(current_detections)
    size = previous_count + current_count
    cost_matrix = np.full(
        (size, size), config.temporal_unmatched_cost, dtype=np.float64
    )
    rejected: dict[tuple[int, int], str] = {}

    for p_index, previous in enumerate(previous_detections):
        for c_index, current in enumerate(current_detections):
            previous_box = previous_boxes[p_index]
            current_box = current.get("bbox")
            if not _valid_bbox(previous_box) or not _valid_bbox(current_box):
                cost_matrix[p_index, c_index] = float("inf")
                rejected[(p_index, c_index)] = "invalid_bounding_box"
                continue
            iou = calculate_iou(previous_box, current_box)
            distance = calculate_center_distance(
                previous_box,
                current_box,
                current_image.shape[1],
                current_image.shape[0],
            )
            if distance > config.temporal_max_normalized_distance:
                cost_matrix[p_index, c_index] = float("inf")
                rejected[(p_index, c_index)] = "excessive_center_distance"
                continue
            if iou < config.temporal_min_spatial_iou and distance > 0.22:
                cost_matrix[p_index, c_index] = float("inf")
                rejected[(p_index, c_index)] = "excessive_spatial_mismatch"
                continue

            previous_product = previous.get("matched_product")
            current_product = current.get("matched_product")
            if previous_product and current_product:
                previous_id = previous_product.get("id")
                current_id = current_product.get("id")
                if previous_id is not None and current_id is not None and previous_id != current_id:
                    cost_matrix[p_index, c_index] = float("inf")
                    rejected[(p_index, c_index)] = "conflicting_catalog_identity"
                    continue

            text_similarity = _text_similarity(previous, current)
            appearance_similarity = calculate_appearance_similarity(
                previous_image,
                previous_box,
                current_image,
                current_box,
            )
            iou_weight = 0.35 * (0.5 if not alignment_available else 1.0)
            distance_weight = 0.30 * (0.5 if not alignment_available else 1.0)
            text_weight = 0.15
            appearance_weight = 0.20 if appearance_similarity > 0.0 else 0.0
            total_weight = iou_weight + distance_weight + text_weight + appearance_weight
            cost = (
                iou_weight * (1.0 - iou)
                + distance_weight * distance
                + text_weight * (1.0 - text_similarity)
                + appearance_weight * (1.0 - appearance_similarity)
            ) / total_weight
            cost_matrix[p_index, c_index] = float(cost)
            if cost > config.temporal_match_cost_threshold:
                rejected[(p_index, c_index)] = "cost_above_acceptance_threshold"

    for p_index in range(previous_count):
        for c_index in range(current_count, size):
            cost_matrix[p_index, c_index] = config.temporal_unmatched_cost
    for p_index in range(previous_count, size):
        for c_index in range(current_count):
            cost_matrix[p_index, c_index] = config.temporal_unmatched_cost
    for p_index in range(previous_count, size):
        for c_index in range(current_count, size):
            cost_matrix[p_index, c_index] = 0.0

    try:
        from scipy.optimize import linear_sum_assignment
        rows, columns = linear_sum_assignment(cost_matrix)
        assignment_method = "hungarian"
    except ImportError:
        assignment_method = "greedy"
        rows = []
        columns = []
        available_rows = set(range(size))
        available_columns = set(range(size))
        while available_rows and available_columns:
            candidates = [
                (float(cost_matrix[row, column]), row, column)
                for row in available_rows
                for column in available_columns
            ]
            cost, row, column = min(candidates)
            rows.append(row)
            columns.append(column)
            available_rows.remove(row)
            available_columns.remove(column)

    matched_previous: set[int] = set()
    matched_current: set[int] = set()
    unchanged: list[dict[str, Any]] = []
    uncertain: list[dict[str, Any]] = []
    for p_index, c_index in zip(rows, columns):
        p_index, c_index = int(p_index), int(c_index)
        if p_index >= previous_count or c_index >= current_count:
            continue
        cost = float(cost_matrix[p_index, c_index])
        if not np.isfinite(cost) or cost > config.temporal_match_cost_threshold:
            uncertain.append({
                "previous_detection": previous_detections[p_index],
                "current_detection": current_detections[c_index],
                "status": "uncertain",
                "reason": rejected.get((p_index, c_index), "low_assignment_confidence"),
            })
            continue
        previous_box = previous_boxes[p_index]
        current_box = current_detections[c_index].get("bbox", [])
        iou = calculate_iou(previous_box, current_box)
        distance = calculate_center_distance(
            previous_box, current_box, current_image.shape[1], current_image.shape[0]
        )
        text_similarity = _text_similarity(
            previous_detections[p_index], current_detections[c_index]
        )
        appearance_similarity = calculate_appearance_similarity(
            previous_image,
            previous_box,
            current_image,
            current_box,
        )
        evidence_count = sum([
            iou >= 0.01,
            np.isfinite(distance),
            text_similarity > 0.0,
            appearance_similarity > 0.0,
        ])
        matched_previous.add(p_index)
        matched_current.add(c_index)
        unchanged.append({
            "previous_detection": previous_detections[p_index],
            "current_detection": current_detections[c_index],
            "match_cost": round(cost, 4),
            "match_confidence": "strong" if evidence_count >= 3 else "limited",
            "iou": round(iou, 4),
            "center_distance": round(distance, 4) if np.isfinite(distance) else None,
            "text_similarity": round(text_similarity, 4),
            "appearance_similarity": round(appearance_similarity, 4),
            "alignment_available": alignment_available,
            "rejection_reason": None,
        })

    disappeared = [
        _temporal_summary(detection)
        for index, detection in enumerate(previous_detections)
        if index not in matched_previous
    ]
    newly_visible = [
        _temporal_summary(detection)
        for index, detection in enumerate(current_detections)
        if index not in matched_current
    ]
    return {
        "enabled": True,
        "method": f"{assignment_method}_{'aligned' if alignment_available else 'uncertain'}",
        "alignment": alignment,
        "alignment_available": alignment_available,
        "unchanged_count": len(unchanged),
        "disappeared_count": len(disappeared),
        "newly_visible_count": len(newly_visible),
        "uncertain_count": len(uncertain),
        "disappeared": disappeared,
        "newly_visible": newly_visible,
        "unchanged": unchanged,
        "uncertain": uncertain,
        "summary": (
            f"{len(disappeared)} potential disappearances and "
            f"{len(newly_visible)} newly visible detections; "
            f"{len(uncertain)} uncertain associations."
        ),
    }


def _temporal_summary(detection: dict[str, Any]) -> dict[str, Any]:
    product = detection.get("matched_product")
    return {
        "label": product["name"] if product else detection.get("label", "Unknown item"),
        "product_id": product["id"] if product else None,
        "model_label": detection.get("model_label"),
        "texts": detection.get("texts", []),
        "bbox": detection.get("bbox", []),
        "confidence": detection.get("confidence"),
        "classification_status": detection.get("classification_status", "unknown"),
    }
