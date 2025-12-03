# safety.py
from typing import Tuple

MAX_INPUT_CHARS = 6000


def validate_user_input(user_text: str) -> Tuple[bool, str]:
    if not user_text or not user_text.strip():
        return False, "Please enter some text or upload a file."

    if len(user_text) > MAX_INPUT_CHARS:
        return False, (
            f"Your input is too long ({len(user_text)} characters). "
            f"Please reduce it below {MAX_INPUT_CHARS} characters."
        )

    lowered = user_text.lower()
    banned_patterns = [
        "ignore previous instructions",
        "jailbreak",
        "system override",
        "forget the above",
    ]
    for pattern in banned_patterns:
        if pattern in lowered:
            return False, "Your input contains unsafe prompt-injection patterns."

    return True, ""
