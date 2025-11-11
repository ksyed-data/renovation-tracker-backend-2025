from ultralytics import YOLO
from PIL import Image
import requests
from io import BytesIO

model = YOLO("yolov8s-cls.pt")
result = model.train(
    data="C:/Capstone Project/renovation-tracker-backend-2025/House_Room_Dataset/train",
    epochs=20,
    imgsz=224,
)
# model = YOLO("yolo_models/best.pt")
# headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
# url = "https://images.homes.com/listings/117/9098238554-761265702/12503-flock-ct-spotsylvania-va-41.jpg"
# getImage = requests.get(url, headers=headers, stream=True, timeout=10)
# image = Image.open(BytesIO(getImage.content))
# results = model.predict(image)


# top5 = results[0].probs.top5
# for i in top5:
#   name = results[0].names[i]
#   score = results[0].probs.data[i].item()
#  print(f"{name}: {score:.2f}")
