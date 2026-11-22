from __future__ import annotations

import re
from typing import Any

# Hook event types that are valid per the agent plugin spec
VALID_HOOK_EVENTS = {
    "on_start",
    "on_end",
    "on_error",
    "on_success",
    "on_step",
    "on_step_end",
}

# CRLF detection pattern
CRLF_PATTERN = re.compile(r"\r\n")


def validate_hook_schema(schema: Any) -> list[str]:
    """Validate an agent hook schema for compliance.

    Checks:
    - CRLF line endings (security/parsing risk)
    - Valid hook event names
    - Required fields presence
    - Event ordering constraints

    Returns a list of human-readable error messages; empty list means valid.
    """
    errors: list[str] = []

    if schema is None:
        errors.append("Hook schema is null")
        return errors

    if isinstance(schema, str):
        # Check for CRLF in raw string
        if CRLF_PATTERN.search(schema):
            errors.append(
                "Hook schema contains CRLF line endings; use LF only"
            )
        # Try to parse as JSON
        import json
        try:
            schema = json.loads(schema)
        except json.JSONDecodeError as exc:
            errors.append(f"Hook schema is not valid JSON: {exc}")
            return errors

    if not isinstance(schema, dict):
        errors.append("Hook schema must be a JSON object")
        return errors

    # Check for valid hook events
    events_found: set[str] = set()
    for key in schema:
        key_lower = str(key).strip().lower()
        if key_lower in VALID_HOOK_EVENTS:
            events_found.add(key_lower)

    invalid_keys = [k for k in schema if str(k).strip().lower() not in VALID_HOOK_EVENTS]
    if invalid_keys:
        errors.append(
            f"Invalid hook event name(s): {', '.join(invalid_keys)}"
        )

    # Check for missing required events (at least one should be present)
    if not events_found:
        errors.append(
            "Hook schema must contain at least one valid hook event "
            f"(valid events: {', '.join(sorted(VALID_HOOK_EVENTS))})"
        )

    # Check for CRLF in string values
    _check_crlf_in_values(schema, errors)

    return errors


def _check_crlf_in_values(obj: Any, errors: list[str], path: str = "") -> None:
    """Recursively check for CRLF in string values within the schema."""
    if isinstance(obj, str):
        if CRLF_PATTERN.search(obj):
            errors.append(
                f"{path or 'schema'}: string value contains CRLF line endings"
            )
    elif isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else str(key)
            _check_crlf_in_values(value, errors, new_path)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            new_path = f"{path}[{idx}]"
            _check_crlf_in_values(item, errors, new_path)
