#!/usr/bin/env python3
"""Verify a KRINEIA JSONL receipt hash chain.

The verifier is intentionally stdlib-only. It validates the v0.1 receipt
envelope described in RECEIPT_SCHEMA.md:

- each line is a JSON object
- required top-level fields are present
- the genesis receipt has prev_hash of 64 zeroes
- each receipt hash matches canonical JSON without the hash field
- each receipt prev_hash links to the prior receipt hash
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("id", "time", "state", "drift", "prev_hash", "hash")
HASH_ZERO = "0" * 64


def canonical_receipt(receipt: dict[str, Any]) -> str:
    """Return the canonical form hashed by KRINEIA receipts."""

    canonical = {
        "id": receipt["id"],
        "time": receipt["time"],
        "state": receipt["state"],
        "drift": receipt["drift"],
        "prev_hash": receipt["prev_hash"],
    }
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_hash(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(char in "0123456789abcdef" for char in value)


def validate_receipt(receipt: object, line_number: int, previous_hash: str | None) -> list[str]:
    errors: list[str] = []

    if not isinstance(receipt, dict):
        return [f"line {line_number}: receipt is not a JSON object"]

    missing = [field for field in REQUIRED_FIELDS if field not in receipt]
    if missing:
        errors.append(f"line {line_number}: missing required fields: {', '.join(missing)}")
        return errors

    extra = sorted(set(receipt) - set(REQUIRED_FIELDS))
    if extra:
        errors.append(f"line {line_number}: unknown top-level fields: {', '.join(extra)}")

    for field in ("prev_hash", "hash"):
        if not is_hash(receipt[field]):
            errors.append(f"line {line_number}: {field} must be 64 lowercase hex characters")

    if previous_hash is None:
        if receipt["prev_hash"] != HASH_ZERO:
            errors.append(f"line {line_number}: genesis prev_hash must be {HASH_ZERO}")
    elif receipt["prev_hash"] != previous_hash:
        errors.append(
            f"line {line_number}: prev_hash {receipt['prev_hash']} does not match prior hash {previous_hash}"
        )

    expected_hash = sha256_hex(canonical_receipt(receipt))
    if receipt["hash"] != expected_hash:
        errors.append(f"line {line_number}: hash mismatch, expected {expected_hash}")

    return errors


def verify_chain(path: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    previous_hash: str | None = None
    count = 0

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            count += 1
            try:
                receipt = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc}")
                continue

            receipt_errors = validate_receipt(receipt, line_number, previous_hash)
            errors.extend(receipt_errors)
            if isinstance(receipt, dict) and is_hash(receipt.get("hash")):
                previous_hash = receipt["hash"]
            else:
                previous_hash = None

    if count == 0:
        errors.append("chain is empty")

    return count, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a KRINEIA JSONL receipt hash chain")
    parser.add_argument("chain", type=Path, help="Path to a KRINEIA .jsonl receipt chain")
    args = parser.parse_args()

    count, errors = verify_chain(args.chain)
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        print(f"KRINEIA chain invalid: {count} receipt(s), {len(errors)} error(s)", file=sys.stderr)
        return 1

    print(f"KRINEIA chain valid: {count} receipt(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
