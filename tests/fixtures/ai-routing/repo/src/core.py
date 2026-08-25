"""Tiny fixture module used by deterministic routing tests."""


def normalize_name(value: str) -> str:
    return value.strip().lower()
