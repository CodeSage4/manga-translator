import requests
import urllib.parse

def mymemory_translator_factory(src="ja", tgt="en"):
    base_url = "https://api.mymemory.translated.net/get"

    def translate(text: str) -> str:
        if not text.strip():
            return ""
        try:
            params = {
                "q": text,
                "langpair": f"{src}|{tgt}",
            }
            url = base_url + "?" + urllib.parse.urlencode(params)
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return r.json()["responseData"]["translatedText"]
        except Exception:
            return "[Translation Error]"

    return translate

# ============================================================
# In Painting
# ============================================================
import textwrap
import cv2
import numpy as np
def render_translations(img, bubbles):
    out = img.copy()

    # -------------------------------
    # 1. Build inpainting mask
    # -------------------------------
    mask = np.zeros(img.shape[:2], dtype=np.uint8)

    for b in bubbles:
        for l in b["lines"]:
            cv2.fillPoly(mask, [l["box"]], 255)

    # Expand mask slightly to fully cover glyph edges
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    mask = cv2.dilate(mask, kernel, iterations=2)

    # Inpaint
    out = cv2.inpaint(out, mask, 3, cv2.INPAINT_TELEA)

    # -------------------------------
    # 2. Render translated text
    # -------------------------------
    font = cv2.FONT_HERSHEY_SIMPLEX

    for b in bubbles:
        text = b.get("en", "").strip()
        if not text:
            continue

        # Use union of glyph boxes, NOT bbox
        pts = np.vstack([l["box"] for l in b["lines"]])
        x1, y1 = pts.min(axis=0)
        x2, y2 = pts.max(axis=0)

        w = x2 - x1
        h = y2 - y1

        # Dynamic font scaling
        font_scale = min(1.0, h / 90)
        thickness = max(1, int(font_scale * 2))

        # Text wrapping heuristic
        chars_per_line = max(5, int(w / (18 * font_scale)))
        wrapped = textwrap.wrap(text, width=chars_per_line)

        # Vertical centering
        total_h = 0
        line_sizes = []
        for line in wrapped:
            (lw, lh), _ = cv2.getTextSize(line, font, font_scale, thickness)
            line_sizes.append((lw, lh))
            total_h += lh + int(8 * font_scale)

        total_h -= int(8 * font_scale)
        y = y1 + (h - total_h) // 2

        # Draw text (white stroke + black fill)
        for (line, (lw, lh)) in zip(wrapped, line_sizes):
            x = x1 + (w - lw) // 2

            # Stroke
            cv2.putText(out, line, (x, y + lh),
                        font, font_scale, (255,255,255),
                        thickness + 3, cv2.LINE_AA)

            # Fill
            cv2.putText(out, line, (x, y + lh),
                        font, font_scale, (0,0,0),
                        thickness, cv2.LINE_AA)

            y += lh + int(8 * font_scale)

    return out

# ============================================================
# OCR VISUALIZATION (DEBUG ONLY) — NOTEBOOK SAFE
# ============================================================

import matplotlib.pyplot as plt

def show_image(img, title="", max_h=720):
    h, w = img.shape[:2]
    if h > max_h:
        scale = max_h / h
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    plt.figure(figsize=(6, 6))
    plt.imshow(img_rgb)
    plt.title(title)
    plt.axis("off")
    plt.show()


def visualize_ocr(img, boxes, texts, title="OCR Result", block=True):
    """
    Same signature as before.
    Internally uses matplotlib instead of cv2.imshow.
    """
    vis = img.copy()
    for box, (_, conf) in zip(boxes, texts):
        color = (0, 255, 0) if conf >= 0.7 else (0, 0, 255)
        cv2.polylines(vis, [box.astype(np.int32)], True, color, 2)

    show_image(vis, title=title)

