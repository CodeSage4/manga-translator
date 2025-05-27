import cv2
import numpy as np
import matplotlib.pyplot as plt
import requests
from paddleocr import PaddleOCR

# Load Image
image_path = r"C:\Users\Lenovo\Downloads\luffy.png"
image = cv2.imread(image_path)
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Initialize OCR
ocr = PaddleOCR(
    use_gpu=False,
    lang='japan',
    det_algorithm='DB',
    rec_algorithm='SVTR_LCNet',
    use_angle_cls=True,
    drop_score=0.05,
    use_space_char=True,
    cls=True
)

# Translation function using MyMemory API
def translate_text(text, src='ja', dest='en'):
    url = "https://api.mymemory.translated.net/get"
    params = {
        'q': text,
        'langpair': f'{src}|{dest}'
    }
    try:
        response = requests.get(url, params=params)
        result = response.json()
        return result['responseData']['translatedText']
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # fallback to original

# Run OCR
result = ocr.ocr(image_path, cls=True)

# Make a copy for drawing
image_bgr_with_translations = cv2.imread(image_path)

print("\nRecognized Text & Translations:\n")
for line in result:
    for box, (text, conf) in line:
        translated = translate_text(text)
        print(f"JP: {text} (Conf: {conf:.2f}) → EN: {translated}")

        # Draw bounding box
        pts = [(int(x), int(y)) for x, y in box]
        cv2.polylines(image_bgr_with_translations, [np.array(pts)], isClosed=True, color=(0, 255, 0), thickness=2)

        # Put translated text on image
        x, y = pts[0]
        cv2.putText(image_bgr_with_translations, translated, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)

# Convert to RGB for Matplotlib
image_rgb_with_translations = cv2.cvtColor(image_bgr_with_translations, cv2.COLOR_BGR2RGB)

# Display final image with translated text
plt.figure(figsize=(12, 10))
plt.imshow(image_rgb_with_translations)
plt.axis('off')
plt.title("OCR with Translated Text Overlay (JA → EN)")
plt.show()
