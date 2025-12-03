import json
import time
import os
import sys
from dotenv import load_dotenv

# ----- Load .env from project root -----
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(ENV_PATH)

# Add project root to Python path
sys.path.append(PROJECT_ROOT)

from app.ocr_utils import extract_text_pdf
from app.llm import generate_summary

def passes(summary, expected_keywords):
    summary_lower = summary.lower()
    return all(word.lower() in summary_lower for word in expected_keywords)


def run_pdf_tests():
    with open("tests/tests_pdfs.json") as f:
        tests = json.load(f)

    passed = 0
    results = []

    print("\n=== PDF TEST SUITE ===\n")

    for test in tests:
        filename = test["file"]
        expect = test["expect"]

        pdf_path = os.path.join("pdf_samples", filename)

        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found: {pdf_path}")
            continue

        print(f"\n📄 Testing PDF: {filename}")

        # Load PDF as bytes
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # --- OCR ---
        t0 = time.time()
        text, method = extract_text_pdf(pdf_bytes)
        t1 = time.time()

        print(f"- OCR method: {method}")
        print(f"- OCR time: {round((t1 - t0) * 1000)} ms")
        print(f"- Extracted text length: {len(text.strip())}")

        # --- LLM summary ---
        t2 = time.time()
        summary, _ = generate_summary(text, [])
        t3 = time.time()

        print(f"- LLM time: {round((t3 - t2) * 1000)} ms")
        print("\n--- SUMMARY OUTPUT ---")
        print(summary)
        print("----------------------\n")

        # --- Evaluate ---
        ok = passes(summary, expect)

        if ok:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            missing = [kw for kw in expect if kw.lower() not in summary.lower()]
            print("Missing:", missing)

        results.append({
            "file": filename,
            "passed": ok,
            "ocr_method": method,
            "latency_ms": round((t3 - t0) * 1000)
        })

    # Write results to JSON
    with open("tests/pdf_test_results.json", "w") as out:
        json.dump(results, out, indent=2)

    print("\n=== FINAL PDF REPORT ===")
    print(f"Pass rate: {passed}/{len(tests)}")
    print("Saved results to tests/pdf_test_results.json")


if __name__ == "__main__":
    run_pdf_tests()
