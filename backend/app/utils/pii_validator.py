"""Validation helpers for preventing PAN/Aadhaar entry in free text."""

import re

PII_FIELD_MESSAGE = "This field appears to contain a PAN or Aadhaar number, which shouldn't be entered here. Please remove it."
PAN_PATTERN = re.compile(r"(?<![A-Z0-9])[A-Z]{5}[0-9]{4}[A-Z](?![A-Z0-9])", re.IGNORECASE)
AADHAAR_PATTERN = re.compile(r"(?<!\d)(?:\d{4}[ -]?){2}\d{4}(?!\d)")


def contains_pan_or_aadhaar(value: str | None) -> bool:
    if not value:
        return False
    return bool(PAN_PATTERN.search(value) or AADHAAR_PATTERN.search(value))


def reject_pii_in_free_text(value: str | None) -> str | None:
    if contains_pan_or_aadhaar(value):
        raise ValueError(PII_FIELD_MESSAGE)
    return value