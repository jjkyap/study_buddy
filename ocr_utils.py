# ocr_utils.py

import io
from typing import Tuple, List

import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
import easyocr
import numpy as np

# English-only, CPU
easyocr_reader = easyocr.Reader(["en"], gpu=False)


# ---------- helpers ----------

def _classify_page(page: pdfplumber.page.Page, text: str) -> str:
    """
    Classify page content type using pdfplumber metadata.

    Returns one of: "text", "scanned", "mixed".
    """
    text_len = len(text.strip())
    # pdfplumber exposes images as page.images
    num_images = len(getattr(page, "images", []))

    if text_len > 150 and num_images == 0:
        return "text"
    if text_len < 30 and num_images > 0:
        return "scanned"
    return "mixed"


def _preprocess_for_ocr(img):
    """
    Light preprocessing to help Tesseract / EasyOCR:
    grayscale + simple binary threshold.
    """
    # pdf2image gives a PIL Image
    img_gray = img.convert("L")
    # simple threshold; tweak value if needed
    img_bin = img_gray.point(lambda x: 0 if x < 180 else 255, "1")
    return img_bin


def _ocr_tesseract(img) -> str:
    try:
        processed = _preprocess_for_ocr(img)
        text = pytesseract.image_to_string(processed)
        return text or ""
    except Exception as e:
        print("Tesseract OCR failed:", e)
        return ""


def _ocr_easyocr(img) -> str:
    try:
        processed = _preprocess_for_ocr(img)
        arr = np.array(processed)
        results = easyocr_reader.readtext(arr, detail=1, paragraph=True)
    except Exception as e:
        print("EasyOCR failed:", e)
        return ""

    lines: List[str] = []
    if not results:
        return ""

    for r in results:
        # r should be (bbox, text, conf)
        try:
            _, text, _ = r
            if text and isinstance(text, str):
                lines.append(text)
        except Exception as e:
            print("Bad EasyOCR result:", r, e)
            continue

    return "\n".join(lines)


# ---------- main API ----------

def extract_text_pdf(pdf_bytes: bytes) -> Tuple[str, str]:
    """
    Hybrid OCR pipeline for mixed PDFs.

    Per page:
      1. Try pdfplumber to get digital text.
      2. Classify page as text / scanned / mixed.
      3. For scanned/mixed pages, run Tesseract (fast),
         and fall back to EasyOCR if Tesseract is weak.
      4. Combine results.

    Returns:
        (full_text: str, method_used: str)
        method_used is one of: "pdfplumber", "hybrid_ocr", "empty", or an error tag.
    """
    all_page_text: List[str] = []
    used_ocr = False

    # First pass: inspect pages with pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            plumber_pages = list(pdf.pages)
            plumber_texts = []

            for page in plumber_pages:
                text = page.extract_text() or ""
                plumber_texts.append(text)

    except Exception as e:
        print("pdfplumber failed during inspection:", e)
        plumber_pages = []
        plumber_texts = []

    # Second pass: convert to images once (for OCR)
    try:
        images = convert_from_bytes(pdf_bytes)
    except Exception as e:
        print("pdf2image failed:", e)
        images = []

    # Ensure we can iterate safely
    num_pages = max(len(plumber_pages), len(images), len(plumber_texts))
    for i in range(num_pages):
        page = plumber_pages[i] if i < len(plumber_pages) else None
        page_text = plumber_texts[i] if i < len(plumber_texts) else ""
        img = images[i] if i < len(images) else None

        if page is None:
            # No pdfplumber page; pure image → OCR
            if img is not None:
                used_ocr = True
                tess_text = _ocr_tesseract(img)
                if len(tess_text.strip()) > 30:
                    all_page_text.append(tess_text)
                else:
                    easy_text = _ocr_easyocr(img)
                    all_page_text.append(easy_text)
            continue

        # Classify the page
        page_type = _classify_page(page, page_text)
        print(f"[OCR] Page {i+1}: type={page_type}, len(text)={len(page_text.strip())}, images={len(getattr(page, 'images', []))}")

        if page_type == "text":
            # pdfplumber is good enough
            all_page_text.append(page_text)
            continue

        # scanned or mixed → need OCR
        used_ocr = True

        # Start with pdfplumber text if any (for mixed pages)
        combined = page_text.strip()

        if img is not None:
            tess_text = _ocr_tesseract(img)
            if len(tess_text.strip()) > 30:
                combined = (combined + "\n" + tess_text).strip()
            else:
                easy_text = _ocr_easyocr(img)
                combined = (combined + "\n" + easy_text).strip()

        all_page_text.append(combined)

    full_text = "\n\n".join(t for t in all_page_text if t and t.strip())

    if not full_text.strip():
        return "", "empty"

    method_used = "hybrid_ocr" if used_ocr else "pdfplumber"
    return full_text, method_used
