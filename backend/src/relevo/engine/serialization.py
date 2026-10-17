"""One canonical UTF-8 JSON encoding for sizes and request/report fingerprints."""

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()
