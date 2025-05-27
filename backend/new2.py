import warnings
import torch.nn.modules.module
from transformers import AutoModel
import numpy as np
from PIL import Image
import torch
import os

# Suppress specific PyTorch warnings
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="torch.nn.modules.module"
)

# Load image paths
images = [
    r"C:\Users\Lenovo\Downloads\manga2.png",
    r"C:\Users\Lenovo\Downloads\manga3.jpg",
]

# Load images as numpy arrays
def read_image_as_np_array(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    with open(image_path, "rb") as file:
        image = Image.open(file).convert("L").convert("RGB")
        image = np.array(image)
    return image

images = [read_image_as_np_array(image) for image in images]

# Load model safely
device = "cuda" if torch.cuda.is_available() else "cpu"
model = AutoModel.from_pretrained(
    "ragavsachdeva/magi",
    trust_remote_code=True,
    low_cpu_mem_usage=False,  # Optional
).to(device)

# Run inference
with torch.no_grad():
    results = model.predict_detections_and_associations(images)
    text_bboxes_for_all_images = [x["texts"] for x in results]
    ocr_results = model.predict_ocr(images, text_bboxes_for_all_images)

# Save visualizations and transcripts
for i in range(len(images)):
    model.visualise_single_image_prediction(
        images[i],
        results[i],
        filename=f"image_{i}.png"
    )
    model.generate_transcript_for_single_image(
        results[i],
        ocr_results[i],
        filename=f"transcript_{i}.txt"
    )
