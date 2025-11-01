"""Helpers for generating short, URL-friendly identifiers."""

from __future__ import annotations

import secrets
import string

ALPHABET = string.ascii_lowercase + string.digits


def generate_short_id(length: int = 9) -> str:
  """Return a random string of ``length`` characters."""
  if length <= 0:
    raise ValueError("length must be positive")
  return "".join(secrets.choice(ALPHABET) for _ in range(length))

