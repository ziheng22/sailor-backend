
import re
from pathlib import Path

def parse_frontmatter(text: str) -> dict:
    lines = text.splitlines()
    data: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        m = re.match(r"^(\w[\w-]*):(?:\s*(.*))?$", line)
        if not m:
            i += 1
            continue

        key, inline = m.group(1), m.group(2)
        if inline is not None and inline.strip():
            val = inline.strip().strip('"').strip("'")
            if val == "[]":
                data[key] = []
            elif val == "true":
                data[key] = True
            elif val == "false":
                data[key] = False
            elif re.match(r"^-?\d+(\.\d+)?$", val):
                data[key] = float(val) if "." in val else int(val)
            else:
                data[key] = val
            i += 1
            continue

        nested_lines = []
        j = i + 1
        while j < len(lines) and lines[j].startswith("  "):
            nested_lines.append(lines[j].strip())
            j += 1

        if nested_lines:
            if nested_lines[0].startswith("- "):
                data[key] = [ln[2:] for ln in nested_lines if ln.startswith("- ")]
            else:
                obj = {}
                for nl in nested_lines:
                    p = re.match(r"^(\w+):\s*(.*)", nl)
                    if p:
                        obj[p.group(1)] = p.group(2).strip().strip('"').strip("'")
                data[key] = obj
        else:
            data[key] = ""

        i = j

    return data

def parse_mdx(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8").lstrip("\ufeff")
    if not raw.startswith("---"):
        return {}, raw.strip()
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw.strip()
    return parse_frontmatter(parts[1]), parts[2].strip()


def _yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "\n".join([f"  - {item}" for item in items])


def write_mdx(path: Path, frontmatter: dict, body: str = "") -> None:
    """\u5c06 frontmatter \u5b57\u5178\u548c\u6b63\u6587\u5199\u5165 MDX \u6587\u4ef6"""
    lines = ["---"]
    for key, value in frontmatter.items():
        if key in ("body", "slug", "status"):
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.append(_yaml_list(value))
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif value is None or value == "":
            lines.append(f'{key}: ""')
        else:
            s = str(value)
            if ":" in s or s.startswith("{") or s.startswith("["):
                s = s.replace('"', '\\"')
                lines.append(f'{key}: "{s}"')
            else:
                lines.append(f"{key}: {s}")
    lines.append("---")
    lines.append("")
    if body:
        lines.append(body.strip())
    else:
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
