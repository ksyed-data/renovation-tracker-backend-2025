from ultralytics import YOLO

model = YOLO("path/to/best.pt")  # load a custom trained model

# Train the model
results = model.train(data="mnist160", epochs=20, imgsz=224)
