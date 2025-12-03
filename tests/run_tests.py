
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
from app.llm import generate_summary

def passes(summary, expected_keywords):
    summary_lower = summary.lower()
    return all(word.lower() in summary_lower for word in expected_keywords)


def run_tests():
    with open("tests/tests.json") as f:
        tests = json.load(f)

    passed = 0
    total = len(tests)

    print("\n=== TEXT TEST SUITE ===\n")

    for test in tests:
        name = test["name"]
        text_input = test["input"]
        expect = test["expect"]

        print(f"\n Test: {name}")

        t0 = time.time()
        summary, _ = generate_summary(text_input, [])
        t1 = time.time()

        ok = passes(summary, expect)

        print(f"- Latency: {round((t1 - t0) * 1000)} ms")
        print(f"- Summary: {summary}")

        if ok:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            missing = [e for e in expect if e.lower() not in summary.lower()]
            print("Missing keywords:", missing)

    print("\n=== FINAL REPORT ===")
    print(f"Pass rate: {passed} / {total}")


if __name__ == "__main__":
    run_tests()
