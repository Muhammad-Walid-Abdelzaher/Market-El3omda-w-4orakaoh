from ultralytics import YOLO

# Load your trained model
model = YOLO("best.pt")

# Run inference on test images (set max_det higher for dense shelf items)
results = model.predict(
    source="1000_F_336952739_ruVkiuC9G45BGIZeR7GglCNQrcWdhFrP.jpg",
    max_det=1000,
    conf=0.25,
    save=True,
    project=r"C:\Users\TUF F16\Downloads\AI Machine Learning\StockVision AI",
    name="stockvision-results"
)