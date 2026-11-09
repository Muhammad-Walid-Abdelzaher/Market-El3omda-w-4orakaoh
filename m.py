"""
shelf_cluster.py
Unsupervised product grouping for shelf crops:
  YOLO boxes -> crops -> DINOv2 embeddings -> cosine clustering -> product IDs

Install (Colab/Kaggle):
    pip install ultralytics transformers scikit-learn faiss-cpu opencv-python pandas tqdm
    pip install easyocr        # optional, only for --ocr naming

Usage:
    python shelf_cluster.py --weights best.pt --images ./shelves --out ./out
    python shelf_cluster.py --weights best.pt --images ./shelves --out ./out --threshold 0.25 --ocr

Tip: run on ALL your shelf images together (not one at a time). Clusters get much
better when the same product appears many times across images.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
from sklearn.cluster import AgglomerativeClustering
from tqdm import tqdm
from transformers import AutoImageProcessor, AutoModel
from ultralytics import YOLO

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


# ----------------------------------------------------------------------------
# 1. Detection + cropping
# ----------------------------------------------------------------------------
def detect_and_crop(yolo, image_paths, conf=0.25, iou=0.6, pad=0.04,
                    min_side=24, imgsz=1280, max_det=600):
    """Run YOLO on each image and return a list of crop records."""
    records, crops = [], []
    for p in tqdm(image_paths, desc="Detecting"):
        img = cv2.imread(str(p))
        if img is None:
            continue
        H, W = img.shape[:2]
        res = yolo.predict(img, conf=conf, iou=iou, imgsz=imgsz,
                           max_det=max_det, verbose=False)[0]
        for i, b in enumerate(res.boxes.xyxy.cpu().numpy()):
            x1, y1, x2, y2 = b
            bw, bh = x2 - x1, y2 - y1
            if min(bw, bh) < min_side:
                continue
            # small padding so edges of the pack are not cut
            x1 = int(max(0, x1 - pad * bw)); x2 = int(min(W, x2 + pad * bw))
            y1 = int(max(0, y1 - pad * bh)); y2 = int(min(H, y2 + pad * bh))
            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            crops.append(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
            records.append({"image": p.name, "box_id": i,
                            "x1": x1, "y1": y1, "x2": x2, "y2": y2})
    return records, crops


# ----------------------------------------------------------------------------
# 2. Embeddings (DINOv2)
# ----------------------------------------------------------------------------
@torch.no_grad()
def embed_crops(crops, model_name="facebook/dinov2-base", batch=64, device=None):
    """CLS + mean-patch embedding, L2-normalised. Returns (N, D) float32."""
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    processor = AutoImageProcessor.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device).eval()
    if device == "cuda":
        model = model.half()

    feats = []
    for i in tqdm(range(0, len(crops), batch), desc="Embedding"):
        chunk = crops[i:i + batch]
        # processor resizes to 224 center-crop by default; disable crop so whole
        # product is kept (we resize the full crop to 224x224).
        inputs = processor(images=chunk, return_tensors="pt",
                           do_center_crop=False,
                           size={"height": 224, "width": 224})
        px = inputs["pixel_values"].to(device)
        if device == "cuda":
            px = px.half()
        out = model(pixel_values=px).last_hidden_state          # (B, 1+P, D)
        cls_tok = out[:, 0]
        patch_mean = out[:, 1:].mean(dim=1)
        f = torch.cat([cls_tok, patch_mean], dim=1).float()
        f = torch.nn.functional.normalize(f, dim=1)
        feats.append(f.cpu().numpy())
    return np.concatenate(feats, axis=0).astype("float32")


# ----------------------------------------------------------------------------
# 3. Clustering
# ----------------------------------------------------------------------------
def cluster_embeddings(emb, threshold=0.30, min_cluster_size=3, reassign_sim=0.70):
    """
    Agglomerative clustering with cosine distance, no need to know K.
    - threshold: max average cosine distance inside a cluster (lower = more, purer clusters)
    - Tiny clusters (< min_cluster_size) are merged into the nearest big cluster if
      similarity >= reassign_sim, otherwise labelled as their own 'rare' product (-1).
    """
    n = len(emb)
    if n == 1:
        return np.zeros(1, dtype=int)
    clu = AgglomerativeClustering(n_clusters=None, metric="cosine",
                                  linkage="average", distance_threshold=threshold)
    labels = clu.fit_predict(emb)

    counts = Counter(labels)
    big = [l for l, c in counts.items() if c >= min_cluster_size]
    if not big:
        return labels

    centroids = {l: emb[labels == l].mean(0) for l in big}
    for l in big:
        centroids[l] /= np.linalg.norm(centroids[l]) + 1e-9
    C = np.stack([centroids[l] for l in big])                    # (K, D)
    big_arr = np.array(big)

    final = labels.copy()
    for idx in np.where(~np.isin(labels, big_arr))[0]:
        sims = C @ emb[idx]
        j = int(sims.argmax())
        final[idx] = big_arr[j] if sims[j] >= reassign_sim else -1

    # relabel to 0..K-1 by size (largest first); -1 stays -1
    order = [l for l, _ in Counter(final[final >= 0]).most_common()]
    remap = {old: new for new, old in enumerate(order)}
    remap[-1] = -1
    return np.array([remap[l] for l in final])


# ----------------------------------------------------------------------------
# 4. Optional: name clusters via OCR majority vote
# ----------------------------------------------------------------------------
def name_clusters_with_ocr(df, crops, max_per_cluster=15):
    try:
        import easyocr
    except ImportError:
        print("easyocr not installed, skipping OCR naming")
        return {}
    reader = easyocr.Reader(["en"], gpu=torch.cuda.is_available(), verbose=False)
    names = {}
    for cid, g in tqdm(df[df.cluster_id >= 0].groupby("cluster_id"), desc="OCR naming"):
        words = Counter()
        for idx in g.index[:max_per_cluster]:
            for _, text, conf in reader.readtext(crops[idx]):
                t = text.strip().lower()
                if conf > 0.4 and len(t) >= 3 and t.isalpha():
                    words[t] += 1
        if words:
            names[cid] = " ".join(w for w, _ in words.most_common(2))
    return names


# ----------------------------------------------------------------------------
# 5. Visual QA helpers
# ----------------------------------------------------------------------------
def save_cluster_montages(df, crops, out_dir, top_k=40, per_cluster=24, tile=96):
    out_dir = Path(out_dir) / "montages"
    out_dir.mkdir(parents=True, exist_ok=True)
    sizes = df[df.cluster_id >= 0].cluster_id.value_counts().head(top_k)
    for cid in sizes.index:
        idxs = df.index[df.cluster_id == cid][:per_cluster]
        cols = 8
        rows = int(np.ceil(len(idxs) / cols))
        canvas = np.full((rows * tile, cols * tile, 3), 255, np.uint8)
        for k, i in enumerate(idxs):
            t = cv2.resize(crops[i], (tile, tile))
            r, c = divmod(k, cols)
            canvas[r * tile:(r + 1) * tile, c * tile:(c + 1) * tile] = t
        cv2.imwrite(str(out_dir / f"cluster_{cid:04d}_n{sizes[cid]}.jpg"),
                    cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))


def save_annotated(df, images_dir, out_dir):
    out_dir = Path(out_dir) / "annotated"
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.RandomState(0)
    palette = {}
    for name, g in df.groupby("image"):
        img = cv2.imread(str(Path(images_dir) / name))
        for _, r in g.iterrows():
            cid = int(r.cluster_id)
            if cid not in palette:
                palette[cid] = tuple(int(x) for x in rng.randint(40, 255, 3))
            col = (128, 128, 128) if cid < 0 else palette[cid]
            cv2.rectangle(img, (r.x1, r.y1), (r.x2, r.y2), col, 2)
            cv2.putText(img, str(cid), (r.x1 + 2, r.y1 + 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)
        cv2.imwrite(str(out_dir / name), img)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True, help="YOLO weights (.pt)")
    ap.add_argument("--images", required=True, help="folder with shelf images")
    ap.add_argument("--out", default="out")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--imgsz", type=int, default=1280)
    ap.add_argument("--model", default="facebook/dinov2-base",
                    help="try facebook/dinov2-small (fast) or dinov2-large (best)")
    ap.add_argument("--threshold", type=float, default=0.30,
                    help="cosine distance cut; lower => more clusters")
    ap.add_argument("--min_cluster", type=int, default=3)
    ap.add_argument("--ocr", action="store_true", help="name clusters via OCR vote")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    paths = sorted(p for p in Path(args.images).iterdir() if p.suffix.lower() in IMG_EXT)
    assert paths, f"no images found in {args.images}"

    yolo = YOLO(args.weights)
    records, crops = detect_and_crop(yolo, paths, conf=args.conf, imgsz=args.imgsz)
    print(f"{len(crops)} crops from {len(paths)} images")

    emb = embed_crops(crops, model_name=args.model)
    np.save(out / "embeddings.npy", emb)

    labels = cluster_embeddings(emb, threshold=args.threshold,
                                min_cluster_size=args.min_cluster)
    df = pd.DataFrame(records)
    df["cluster_id"] = labels

    if args.ocr:
        names = name_clusters_with_ocr(df, crops)
        df["cluster_name"] = df.cluster_id.map(names).fillna("")
    else:
        df["cluster_name"] = ""

    df.to_csv(out / "assignments.csv", index=False)
    summary = {
        "n_crops": int(len(df)),
        "n_clusters": int((df.cluster_id >= 0).pipe(lambda m: df.cluster_id[m].nunique())),
        "n_unassigned": int((df.cluster_id < 0).sum()),
        "largest_clusters": df[df.cluster_id >= 0].cluster_id.value_counts().head(10).to_dict(),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

    save_cluster_montages(df, crops, out)
    save_annotated(df, args.images, out)
    print(f"Done. Open {out}/montages to sanity-check clusters.")


if __name__ == "__main__":
    main()