import json
from typing import List

from llm import generate_summary, generate_flashcards


def run_tests(path: str = "tests.json") -> None:
    with open(path, "r", encoding="utf-8") as f:
        tests = json.load(f)

    passed = 0
    total = len(tests)

    for i, test in enumerate(tests, start=1):
        note_text: str = test["input"]
        expected_patterns: List[str] = test.get("expected_contains", [])

        # For offline eval, we can just treat context as empty or [note_text]
        context_chunks = [note_text]

        summary, _ = generate_summary(note_text, context_chunks)
        cards, _ = generate_flashcards(note_text, context_chunks)

        combined_output = summary + "\n" + "\n".join(
            f"Q: {c.get('question', '')} A: {c.get('answer', '')}" for c in cards
        )

        ok = all(pat.lower() in combined_output.lower() for pat in expected_patterns)
        if ok:
            passed += 1

        print(f"Test {i}/{total}: {'PASS' if ok else 'FAIL'}")

    pass_rate = (passed / total) * 100 if total > 0 else 0.0
    print(f"\nPass rate: {passed}/{total} = {pass_rate:.1f}%")

if __name__ == "__main__":
    run_tests()
