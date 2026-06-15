#!/usr/bin/env python3
"""Encode diagram source for Kroki GET URLs (deflate + base64url)."""

import base64
import sys
import zlib


def encode(text: str) -> str:
    compressed = zlib.compress(text.encode("utf-8"), 9)
    return base64.b64encode(compressed).decode("ascii").replace("+", "-").replace("/", "_")


def url(base: str, diagram_type: str, source: str, fmt: str = "svg") -> str:
    base = base.rstrip("/")
    return f"{base}/{diagram_type}/{fmt}/{encode(source)}"


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "https://kroki.thetamind.ai"
    kind = sys.argv[2] if len(sys.argv) > 2 else "plantuml"
    source = sys.stdin.read()
    print(url(base, kind, source))
