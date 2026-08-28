"""Tiny best-effort parser for a Dive's `REQUIRED_DATABASES` export.

A Dive's required resources (which databases/shares its SQL reads) live in
its .tsx source, in the `export const REQUIRED_DATABASES = [...]` block the
Dive runtime itself requires - not in metadata.json - so there is exactly
one place they can drift out of sync. This intentionally does not do a
full TS/JSX parse; it only needs to find `path: '...'` / `alias: '...'`
pairs inside that one block.
"""
from __future__ import annotations

import re

_BLOCK = re.compile(
    r"REQUIRED_DATABASES\s*(?::\s*[^=]+)?=\s*\[(?P<body>.*?)\]\s*;", re.DOTALL
)
_OBJECT = re.compile(r"\{[^{}]*\}", re.DOTALL)
_PATH = re.compile(r"""path\s*:\s*['"]([^'"]*)['"]""")
_ALIAS = re.compile(r"""alias\s*:\s*['"]([^'"]*)['"]""")


def extract_required_databases(source: str) -> list[dict[str, str]]:
    """Return [{"url": ..., "alias": ...}, ...] parsed from the source.

    Raises ValueError with a clear message if the block is missing or an
    entry can't be parsed, rather than silently deploying wrong resources.
    """
    match = _BLOCK.search(source)
    if not match:
        raise ValueError(
            "could not find `export const REQUIRED_DATABASES = [...]` in the dive source"
        )

    resources = []
    for obj in _OBJECT.findall(match.group("body")):
        path_match = _PATH.search(obj)
        alias_match = _ALIAS.search(obj)
        if not path_match or not alias_match:
            raise ValueError(f"malformed REQUIRED_DATABASES entry: {obj.strip()!r}")
        resources.append({"url": path_match.group(1), "alias": alias_match.group(1)})

    if not resources:
        raise ValueError("REQUIRED_DATABASES is empty")
    return resources
