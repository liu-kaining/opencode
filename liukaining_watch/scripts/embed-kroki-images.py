#!/usr/bin/env python3
"""Insert Kroki links + PlantUML source in fenced code blocks."""

import re
import subprocess
import sys
from pathlib import Path

KROKI_BASE = "https://kroki.thetamind.ai"
SCRIPT_DIR = Path(__file__).resolve().parent
ENCODE = SCRIPT_DIR / "kroki-url.py"

KROKI_OLD_RE = re.compile(
    r"<!-- kroki:\d+[^>]*-->\n"
    r"!\[[^\]]*\]\([^\)]+\)\n\n"
    r"<details>\n<summary>[^<]*</summary>\n\n"
    r"(```(?:plantuml|mermaid)\n.*?\n```)\n\n"
    r"</details>\n\n",
    re.DOTALL,
)

KROKI_NEW_RE = re.compile(
    r"<!-- kroki:\d+[^>]*-->\n\n"
    r"\*\*图 ·[^\n]*\*\*\n\n"
    r"Kroki SVG 链接[^\n]*\n\n"
    r"```text\n.*?\n```\n\n"
    r"(?:PlantUML|Mermaid) 源码：\n\n"
    r"(```(?:plantuml|mermaid)\n.*?\n```)\n\n",
    re.DOTALL,
)


def kroki_url(diagram_type: str, source: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(ENCODE), KROKI_BASE, diagram_type],
        input=source,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def verify_url(url: str) -> bool:
    proc = subprocess.run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-A", "Mozilla/5.0", url],
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip() == "200"


def format_block(idx: int, alt: str, lang: str, body: str, url: str, ok: bool) -> str:
    lang_label = "PlantUML" if lang == "plantuml" else "Mermaid"
    status = "ok" if ok else "verify-failed"
    return (
        f"<!-- kroki:{idx} {status} -->\n\n"
        f"**图 · {alt}**\n\n"
        f"Kroki SVG 链接（复制到浏览器打开）：\n\n"
        f"```text\n{url}\n```\n\n"
        f"{lang_label} 源码：\n\n"
        f"```{lang}\n{body}```\n\n"
    )


def strip_embeds(content: str) -> str:
    content = KROKI_OLD_RE.sub(r"\1\n\n", content)
    content = KROKI_NEW_RE.sub(r"\1\n\n", content)
    return content


def embed(content: str) -> str:
    content = strip_embeds(content)
    last_heading = "diagram"
    lines = content.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    n = len(lines)
    diagram_idx = 0

    while i < n:
        line = lines[i]
        if line.startswith("## "):
            last_heading = line[3:].strip().split("（")[0].split("(")[0].strip()
        if line.startswith("### "):
            last_heading = line[4:].strip().split("（")[0].split("(")[0].strip()

        if line.startswith("```plantuml") or line.startswith("```mermaid"):
            lang = "plantuml" if line.startswith("```plantuml") else "mermaid"
            body_lines = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                body_lines.append(lines[i])
                i += 1
            body = "".join(body_lines).rstrip("\n") + "\n"
            i += 1

            diagram_idx += 1
            alt = last_heading.replace('"', "'")
            img_url = kroki_url(lang, body)
            ok = verify_url(img_url)
            out.append(format_block(diagram_idx, alt, lang, body, img_url, ok))
            continue

        out.append(line)
        i += 1

    return "".join(out)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "OpenCode架构图解.md"
    updated = embed(path.read_text(encoding="utf-8"))
    path.write_text(updated, encoding="utf-8")
    print(f"Updated {path} — {updated.count('<!-- kroki:')} Kroki blocks ({KROKI_BASE})")


if __name__ == "__main__":
    main()
