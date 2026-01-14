# ============================================================
# manga_translate.py
# ============================================================

import os
import cv2
import numpy as np
from typing import List, Tuple, Callable, Dict

# ---------------- OCR (PaddleOCR assumed) ----------------
from paddleocr import PaddleOCR

# ---------------- Optional geometry ----------------
from shapely.geometry import Polygon

# ============================================================
# CONFIG
# ============================================================

OCR_CONFIG = dict(
    use_gpu=False,
    lang="japan",
    det_algorithm="DB",
    det_db_thresh=0.2,
    det_db_box_thresh=0.3,
    det_db_unclip_ratio=2.0,
    use_angle_cls=True,
    drop_score=0.1,
    rec_algorithm="SVTR_LCNet",
    use_space_char=False,
)

# ============================================================
# Preprocessing
# ============================================================



# ============================================================
# OCR PREPROCESSING
# ============================================================

def preprocess_for_ocr(img: np.ndarray):
    """
    Returns multiple image variants to improve OCR robustness.
    """
    variants = []

    # --- original ---
    variants.append(img)

    # --- inverted (for white text on black) ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    inv = 255 - gray
    inv_bgr = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
    variants.append(inv_bgr)

    return variants




# ============================================================
# OCR
# ============================================================

def run_ocr(img: np.ndarray, ocr: PaddleOCR):
    res = ocr.ocr(img, cls=True)
    if not res or not res[0]:
        return []
    out = []
    for box, (text, conf) in res[0]:
        box = np.asarray(box, dtype=np.int32)
        if box.shape[0] >= 4:
            out.append((box, text, conf))
    return out


# ============================================================
# OCR CLEANUP (geometry-safe)
# ============================================================


from rapidfuzz import fuzz
from shapely.geometry import Polygon
def is_vertical_box(box, ratio=1.5):
    """
    Heuristic: vertical Japanese text lines are much taller than wide
    """
    w = box[:, 0].max() - box[:, 0].min()
    h = box[:, 1].max() - box[:, 1].min()
    return h > ratio * w


def poly_iou(b1, b2):
    p1 = Polygon(b1)
    p2 = Polygon(b2)

    if not p1.is_valid or not p2.is_valid:
        return 0.0

    inter = p1.intersection(p2).area
    union = p1.union(p2).area + 1e-6
    return inter / union


def box_area(b):
    return (b[:, 0].max() - b[:, 0].min()) * (b[:, 1].max() - b[:, 1].min())


def is_contained(inner, outer, margin=4):
    xi1, yi1 = inner[:, 0].min(), inner[:, 1].min()
    xi2, yi2 = inner[:, 0].max(), inner[:, 1].max()

    xo1, yo1 = outer[:, 0].min(), outer[:, 1].min()
    xo2, yo2 = outer[:, 0].max(), outer[:, 1].max()

    return (
        xi1 >= xo1 - margin and
        yi1 >= yo1 - margin and
        xi2 <= xo2 + margin and
        yi2 <= yo2 + margin
    )


def clean_ocr_results(
    boxes,
    texts,
    iou_thresh=0.25,
    text_sim_thresh=70,
    area_ratio_thresh=0.33,
):
    """
    OCR Cleanup:
    1. Remove duplicates (polygon IoU OR text similarity)
    2. Remove fragment boxes contained in larger ones
    """

    # --------------------------------------------------
    # Stage 1: Deduplicate (normal vs inverted OCR)
    # --------------------------------------------------
    dedup = []

    for box, (txt, conf) in zip(boxes, texts):
        replaced = False

        for i, (fb, ftxt, fconf) in enumerate(dedup):
            if (
                poly_iou(box, fb) > iou_thresh or
                fuzz.ratio(txt, ftxt) > text_sim_thresh
            ):
                # keep higher-confidence detection
                if conf > fconf:
                    dedup[i] = (box, txt, conf)
                replaced = True
                break

        if not replaced:
            dedup.append((box, txt, conf))

    # --------------------------------------------------
    # Stage 2: Fragment / containment suppression
    # --------------------------------------------------
    final = []

    for i, (b, txt, conf) in enumerate(dedup):
        suppress = False

        for j, (bb, tt, cc) in enumerate(dedup):
            if i == j:
                continue

            if is_contained(b, bb):
                sim = fuzz.ratio(txt, tt)

                if (
                    sim < 60 and
                    box_area(b) < area_ratio_thresh * box_area(bb) and
                    conf <= cc
                ):
                    suppress = True
                    break

        if not suppress:
            final.append((b, txt, conf))

    clean_boxes = [b for b, _, _ in final]
    clean_texts = [(t, c) for _, t, c in final]

    return clean_boxes, clean_texts


# ============================================================
# BUBBLE GROUPING (container-based)
# ============================================================

def expand_box(box, pad, vertical=False):
    xs = box[:,0]
    ys = box[:,1]

    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()

    if vertical:
        return (x1 - pad, y1 - pad*2, x2 + pad, y2 + pad*2)
    else:
        return (x1 - pad*2, y1 - pad, x2 + pad*2, y2 + pad)



def boxes_overlap(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)





# ============================================================
# READING ORDER
# ============================================================

def sort_bubbles_manga_order(groups, row_tolerance_percent=0.1):
    """
    Sorts bubbles in strict Manga order (Top-to-Bottom, then Right-to-Left).
    """
    # 1. Sort by Y-coordinate first (Top to Bottom)
    # We use the center Y of the box
    groups.sort(key=lambda g: (g["bbox"][1] + g["bbox"][3]) / 2)
    
    if not groups:
        return []

    sorted_groups = []
    current_row = []
    
    # Get the height of the first box to estimate row tolerance
    first_h = groups[0]["bbox"][3] - groups[0]["bbox"][1]
    tol = first_h * row_tolerance_percent
    
    current_y = (groups[0]["bbox"][1] + groups[0]["bbox"][3]) / 2

    for g in groups:
        cy = (g["bbox"][1] + g["bbox"][3]) / 2
        
        # If this bubble is significantly lower than the current row, flush the row
        row_gap = max(20, tol * 1.5)
        if cy > current_y + row_gap:
            # Sort current row Right-to-Left
            current_row.sort(key=lambda b: -((b["bbox"][0] + b["bbox"][2])/2))
            sorted_groups.extend(current_row)
            
            current_row = [g]
            current_y = cy
        else:
            current_row.append(g)
            
    # Flush final row
    current_row.sort(key=lambda b: -((b["bbox"][0] + b["bbox"][2])/2))
    sorted_groups.extend(current_row)
    
    return sorted_groups




# ============================================================
# TRANSLATION BACKENDS
# ============================================================
import requests
import urllib.parse

def mymemory_translator_factory(
    src="ja",
    tgt="en",
    email=None  # optional, improves quota slightly
):
    base_url = "https://api.mymemory.translated.net/get"

    def translate(text: str) -> str:
        if not text.strip():
            return ""

        params = {
            "q": text,
            "langpair": f"{src}|{tgt}",
        }
        if email:
            params["de"] = email

        try:
            url = base_url + "?" + urllib.parse.urlencode(params)
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            return data["responseData"]["translatedText"]
        except Exception as e:
            print("MyMemory error:", e)
            return "[Translation Error]"

    return translate

def dummy_translator(text: str) -> str:
    """No-LLM fallback"""
    return text


# ============================================================
# TRANSLATION BACKEND (LIGHTWEIGHT / RAM-SAFE)
# ============================================================
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

def helsinki_translator_factory(
    model_name="Helsinki-NLP/opus-mt-ja-en", 
):
    """
    Super-lightweight translator (~300MB RAM).
    Runs easily on CPU.
    """
    print(f"Loading {model_name}...")
    
    # 1. Load Tokenizer & Model
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    except Exception as e:
        print(f"Error loading model: {e}")
        return lambda x: "[Model Load Error]"

    # 2. Create Pipeline
    # device=-1 forces CPU (prevents VRAM crashes)
    translator_pipeline = pipeline(
        "translation", 
        model=model, 
        tokenizer=tokenizer, 
        device=-1 
    )

    def translate(text: str) -> str:
        if not text or not text.strip():
            return ""
        
        try:
            # Helsinki is a direct translation model
            output = translator_pipeline(text, max_length=400)
            # Output format: [{'translation_text': 'Hello world'}]
            return output[0]['translation_text']
        except Exception as e:
            print(f"Translation failed for '{text[:10]}...': {e}")
            return "[Translation Error]"

    print("✅ Local AI Loaded (Helsinki).")
    return translate





def gemini_translator_factory():
    """
    OPTIONAL Gemini backend.
    Requires google-genai AND a key with generateContent access.
    """
    from google import genai
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    def translate(text: str) -> str:
        if not text.strip():
            return ""
        response = client.models.generate_content(
            model="models/gemini-pro",
            contents=text,
            config={"temperature": 0.3, "max_output_tokens": 120},
        )
        return response.text.strip() if response.text else ""

    return translate

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



# ============================================================
# OCR SIDE-BY-SIDE VISUALIZATION (DEBUG) — NOTEBOOK SAFE
# ============================================================

def draw_boxes(img, boxes, texts):
    vis = img.copy()
    for box, (_, conf) in zip(boxes, texts):
        color = (0, 255, 0) if conf >= 0.7 else (0, 0, 255)
        cv2.polylines(vis, [box.astype(np.int32)], True, color, 2)
    return vis


def resize_to_fit(img, max_h=720):
    h, w = img.shape[:2]
    if h <= max_h:
        return img
    scale = max_h / h
    return cv2.resize(img, (int(w * scale), int(h * scale)))


def visualize_ocr_side_by_side(
    img_original,
    img_inverted,
    boxes_orig, texts_orig,
    boxes_inv, texts_inv,
    boxes_merged, texts_merged,
    block=True
):
    """
    Same signature as before.
    Renders inline in notebook instead of opening windows.
    """

    vis_orig = resize_to_fit(draw_boxes(img_original, boxes_orig, texts_orig))
    vis_inv = resize_to_fit(draw_boxes(img_inverted, boxes_inv, texts_inv))
    vis_merged = resize_to_fit(draw_boxes(img_original, boxes_merged, texts_merged))

    imgs = [vis_orig, vis_inv, vis_merged]
    titles = ["Original OCR", "Inverted OCR", "Merged OCR"]

    plt.figure(figsize=(18, 6))
    for i, (img, title) in enumerate(zip(imgs, titles)):
        plt.subplot(1, 3, i + 1)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(title)
        plt.axis("off")

    plt.show()


# ============================================================
# PIPELINE
# ============================================================


def process_page(
    img: np.ndarray,
    translator: Callable[[str], str],
    debug: bool = False,
):
    ocr = PaddleOCR(**OCR_CONFIG)

    # Define scale factor explicitly so we can reverse it later
    SCALE_FACTOR = 1.8

    img_up = cv2.resize(
        img,
        None,
        fx=SCALE_FACTOR,
        fy=SCALE_FACTOR,
        interpolation=cv2.INTER_CUBIC,
    )

    # -------- dual OCR pass --------
    raw_boxes = []
    raw_texts = []

    orig_boxes, orig_texts = [], []
    inv_boxes, inv_texts = [], []

    variants = preprocess_for_ocr(img_up)

    for idx, variant in enumerate(variants):
        ocr_res = run_ocr(variant, ocr)
        for box, text, conf in ocr_res:
            raw_boxes.append(box)
            raw_texts.append((text, conf))

            if idx == 0:  # original
                orig_boxes.append(box)
                orig_texts.append((text, conf))
            else:         # inverted
                inv_boxes.append(box)
                inv_texts.append((text, conf))

    # cleanup
    boxes, texts = clean_ocr_results(raw_boxes, raw_texts)
    lines = []
    for box, (text, conf) in zip(boxes, texts):
        lines.append({
            "box": box,
            "text": text,
            "conf": conf,
            "vertical": is_vertical_box(box),
        })




    # DEBUG: visualize merged OCR (on the upscaled image)
    if debug:
        visualize_ocr_side_by_side(img_original=img_up,
            img_inverted=variants[1],
            boxes_orig=orig_boxes,
            texts_orig=orig_texts,
            boxes_inv=inv_boxes,
            texts_inv=inv_texts,
            boxes_merged=boxes,
            texts_merged=texts,
            block=True)
    


    all_pts = np.vstack(boxes)
    img_h = all_pts[:,1].max() - all_pts[:,1].min()
    pad = max(5, int(img_h * 0.02))

    # bubble grouping
    groups = []
    for l in lines:
        groups.append({
            "bbox": expand_box(l["box"], pad, l["vertical"]),
            "lines": [l]
        })

    # ---- MERGE ----
    merged = True
    while merged:
        merged = False
        new_groups = []

        while groups:
            g = groups.pop(0)
            i = 0
            while i < len(groups):
                if boxes_overlap(g["bbox"], groups[i]["bbox"]):
                    # merge groups
                    g["lines"].extend(groups[i]["lines"])

                    x1, y1, x2, y2 = g["bbox"]
                    ox1, oy1, ox2, oy2 = groups[i]["bbox"]
                    g["bbox"] = (
                        min(x1, ox1),
                        min(y1, oy1),
                        max(x2, ox2),
                        max(y2, oy2),
                    )

                    groups.pop(i)
                    merged = True
                else:
                    i += 1

            new_groups.append(g)

        groups = new_groups

    # ---- SORT AFTER MERGE ----    
    groups = sort_bubbles_manga_order(groups)
    
    results = []

    for g in groups:
        total_area = sum(box_area(l["box"]) for l in g["lines"])
        vertical_area = sum(
            box_area(l["box"]) for l in g["lines"] if l["vertical"]
        )

        if total_area == 0:
            vertical_ratio = 0
        else:
            vertical_ratio = vertical_area / total_area


        if vertical_ratio > 0.5:
            # Japanese vertical reading
            ordered = sorted(
                g["lines"],
                key=lambda l: (-np.mean(l["box"][:,0]), np.mean(l["box"][:,1]))
            )
        else:
            # Horizontal reading
            ordered = sorted(
                g["lines"],
                key=lambda l: (np.mean(l["box"][:,1]), np.mean(l["box"][:,0]))
            )

        raw_text = "".join(l["text"] for l in ordered)

        translated = translator(raw_text)

        # --- FIX: DOWNSCALE COORDINATES ---
        # Convert 1.8x coordinates back to 1.0x coordinates
        # g["bbox"] is (x1, y1, x2, y2)
        x1, y1, x2, y2 = g["bbox"]
        
        corrected_bbox = (
            int(x1 / SCALE_FACTOR),
            int(y1 / SCALE_FACTOR),
            int(x2 / SCALE_FACTOR),
            int(y2 / SCALE_FACTOR)
        )

        scaled_lines = []
        for l in g["lines"]:
            scaled_box = (l["box"] / SCALE_FACTOR).astype(np.int32)
            scaled_lines.append({
                **l,
                "box": scaled_box
            })

        results.append({
            "bbox": corrected_bbox,
            "lines": scaled_lines,   # ✅ SAME COORDINATE SPACE
            "jp": raw_text,
            "en": translated,
        })



    return results


# ============================================================
# In Painting
# ============================================================
import textwrap
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
# ENTRY POINT (TEMP LOCAL IMAGE)
# ============================================================

if __name__ == "__main__":
# ============================================================
# TEMP: LOCAL IMAGE (REPLACE LATER WITH UPLOAD)
# ============================================================
    
    IMAGE_PATH = r"C:\Users\User\Desktop\ocr-manga-translation\manga-translator\backend\uploads\manga3.jpg"

    img = cv2.imread(IMAGE_PATH)
    if img is None:
        raise RuntimeError(f"Failed to load image: {IMAGE_PATH}")

    # --- choose translator ---
    # translator = dummy_translator   # no LLM
    # translator = gemini_translator_factory()  # requires Gemini access
    #translator = nllb_translator_factory()
    translator = mymemory_translator_factory()
    import gc
    gc.collect()


    #translator = helsinki_translator_factory()
    print(translator("お目が高いな"))

    



    bubbles = process_page(img, translator, debug=True)
    rendered = render_translations(img, bubbles)
    show_image(rendered, "Final Rendered Translation")

    for i, b in enumerate(bubbles):
        print(f"\nBubble {i}")
        print("JP:", b["jp"])
        print("EN:", b["en"])
