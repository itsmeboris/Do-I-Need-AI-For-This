"""Parse and render checked architecture verdicts.

The module is deliberately standard-library only so the same artifact pipeline
can run in Claude's code-execution sandbox and in local developer tools.
"""

from __future__ import annotations

import html
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Sequence

from check_verdict import check_verdict


_SKILL_DIR = Path(__file__).resolve().parent
_TEMPLATE_PATH = _SKILL_DIR / "framework" / "verdict-template.md"
_TIERS_PATH = _SKILL_DIR / "framework" / "model-tiers.md"
_OPTIONAL_MARKERS = ("audit entry point only", "multi-unit audits only")


class VerdictRenderError(ValueError):
    """Raised when a verdict cannot be represented safely and completely."""


@dataclass(frozen=True)
class MarkdownSection:
    title: str
    body: str


@dataclass(frozen=True)
class VerdictDocument:
    title: str
    sections: tuple[MarkdownSection, ...]


@dataclass(frozen=True)
class SummaryMetrics:
    judgment_steps: int
    tiers: tuple[str, ...]
    human_gate: bool
    audited_units: int | None
    unaudited_units: int | None


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")


def _section_slug(title: str) -> str:
    """Return one canonical slug, accepting the template's optional annotations."""

    lowered = title.lower().strip()
    for marker in _OPTIONAL_MARKERS:
        suffix = f" ({marker})"
        if lowered.endswith(suffix):
            title = title[: -len(suffix)]
            break
    return _slugify(title)


def _headings(text: str, level: int) -> list[tuple[str, int]]:
    marker = "#" * level + " "
    headings: list[tuple[str, int]] = []
    fenced = False
    for index, line in enumerate(text.split("\n")):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and line.startswith(marker):
            headings.append((line[len(marker) :].strip(), index))
    return headings


def _template_sections() -> tuple[tuple[str, str, bool], ...]:
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    sections = []
    for title, _ in _headings(template, 2):
        lowered = title.lower()
        optional = any(marker in lowered for marker in _OPTIONAL_MARKERS)
        display = re.sub(r"\s*\([^)]*only\)\s*$", "", title, flags=re.IGNORECASE)
        sections.append((display, _slugify(display), optional))
    return tuple(sections)


def _tier_names() -> tuple[str, ...]:
    text = _TIERS_PATH.read_text(encoding="utf-8")
    return tuple(title for title, _ in _headings(text, 2) if title.isupper())


def parse_verdict(markdown: str) -> VerdictDocument:
    """Parse one verdict and enforce the framework's canonical section shape."""

    text = _normalize_newlines(markdown)
    title_headings = _headings(text, 1)
    if len(title_headings) != 1:
        raise VerdictRenderError("verdict must contain exactly one level-1 title")

    lines = text.split("\n")
    found = _headings(text, 2)
    canonical = _template_sections()
    canonical_by_slug = {slug: (title, index) for index, (title, slug, _) in enumerate(canonical)}

    seen: dict[str, str] = {}
    ordered_indices: list[int] = []
    for actual_title, _ in found:
        slug = _section_slug(actual_title)
        if slug not in canonical_by_slug:
            continue
        display, canonical_index = canonical_by_slug[slug]
        if slug in seen:
            raise VerdictRenderError(f"duplicate canonical section: {display}")
        seen[slug] = actual_title
        ordered_indices.append(canonical_index)

    for display, slug, optional in canonical:
        if not optional and slug not in seen:
            raise VerdictRenderError(f"missing required section: {display}")
    if ordered_indices != sorted(ordered_indices):
        raise VerdictRenderError("canonical sections are out of order")

    sections: list[MarkdownSection] = []
    for index, (section_title, start) in enumerate(found):
        end = found[index + 1][1] if index + 1 < len(found) else len(lines)
        body = "\n".join(lines[start + 1 : end]).strip()
        sections.append(MarkdownSection(section_title, body))

    return VerdictDocument(title_headings[0][0], tuple(sections))


def _section(document: VerdictDocument, title: str) -> MarkdownSection | None:
    wanted = _section_slug(title)
    return next((section for section in document.sections if _section_slug(section.title) == wanted), None)


def _split_pipe_cells(line: str) -> list[str]:
    """Split a Markdown pipe row without treating pipes in code spans as cells."""

    content = line.strip().strip("|")
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    for character in content:
        if character == "`":
            in_code = not in_code
            current.append(character)
        elif character == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    cells.append("".join(current).strip())
    return cells


def _table_rows(body: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        if re.fullmatch(r"[-|:\s]+", stripped):
            continue
        rows.append([cell.strip().strip("`") for cell in _split_pipe_cells(stripped)])
    return rows


def _structured_decomposition(document: VerdictDocument) -> list[tuple[str, tuple[str, ...]]]:
    """Return labels and tiers from decomposition rows, excluding commentary."""

    records: list[tuple[str, tuple[str, ...]]] = []
    decomposition = _section(document, "Decomposition")
    if decomposition is not None:
        rows = _table_rows(decomposition.body)
        if rows:
            headers = [_slugify(cell) for cell in rows[0]]
            try:
                label_at = headers.index("label")
            except ValueError as error:
                raise VerdictRenderError("decomposition table is missing the label column") from error
            tier_at = headers.index("tier") if "tier" in headers else None
            for row in rows[1:]:
                if len(row) != len(headers):
                    raise VerdictRenderError("decomposition table row has the wrong number of columns")
                label = row[label_at].strip().upper()
                tiers = ()
                if tier_at is not None:
                    tiers = tuple(tier for tier in _tier_names() if re.search(rf"\b{re.escape(tier)}\b", row[tier_at]))
                records.append((label, tiers))

    unit_verdicts = _section(document, "Unit verdicts")
    if unit_verdicts is not None:
        tier_names = _tier_names()
        for line in unit_verdicts.body.splitlines():
            match = re.match(r"^\s*[-*]\s+\*\*Decomposition:\*\*\s*(.*)$", line, re.IGNORECASE)
            if match is None:
                continue
            body = match.group(1)
            tiers = tuple(tier for tier in tier_names if re.search(rf"\b{re.escape(tier)}\b", body))
            records.extend(("JUDGMENT", tiers) for _ in re.finditer(r"\bJUDGMENT\b", body))
            records.extend(("HUMAN", ()) for _ in re.finditer(r"\bHUMAN\b", body))
    return records


def derive_metrics(document: VerdictDocument) -> SummaryMetrics:
    """Derive report summary values exclusively from parsed verdict content."""

    records = _structured_decomposition(document)
    judgment_records = [tiers for label, tiers in records if label == "JUDGMENT"]
    judgment_steps = len(judgment_records)
    tiers: list[str] = []
    for record_tiers in judgment_records:
        for tier in record_tiers:
            if tier not in tiers:
                tiers.append(tier)

    inventory = _section(document, "Inventory")
    audited_units: int | None = None
    unaudited_units: int | None = None
    if inventory is not None:
        rows = _table_rows(inventory.body)
        if rows:
            headers = [_slugify(cell) for cell in rows[0]]
            try:
                audited_at = headers.index("audited")
            except ValueError as error:
                raise VerdictRenderError("inventory table is missing the audited column") from error
            values = [row[audited_at].lower() for row in rows[1:] if len(row) > audited_at]
            audited_units = values.count("yes")
            unaudited_units = values.count("no")

    return SummaryMetrics(
        judgment_steps=judgment_steps,
        tiers=tuple(tiers),
        human_gate=any(label == "HUMAN" for label, _ in records),
        audited_units=audited_units,
        unaudited_units=unaudited_units,
    )


def _inline(text: str) -> str:
    """Render a deliberately small, escaped subset of inline Markdown."""

    rendered = html.escape(text, quote=True)
    rendered = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", rendered)

    def evidence(match: re.Match[str]) -> str:
        kind = match.group(1).lower()
        css_class = "measurement" if kind == "measured" else "assumption"
        return f'<span class="evidence {css_class}">{match.group(0)}</span>'

    return re.sub(r"\[(assumed|measured):[^\]\n]+\]", evidence, rendered, flags=re.IGNORECASE)


def _pipe_cells(line: str) -> list[str]:
    return _split_pipe_cells(line)


def _is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return (
        lines[index].strip().startswith("|")
        and lines[index].strip().endswith("|")
        and bool(re.fullmatch(r"[-|:\s]+", lines[index + 1].strip()))
    )


def _render_table(lines: list[str], index: int) -> tuple[str, int]:
    headers = _pipe_cells(lines[index])
    index += 2
    rows: list[list[str]] = []
    while index < len(lines):
        line = lines[index].strip()
        if not (line.startswith("|") and line.endswith("|")):
            break
        rows.append(_pipe_cells(line))
        index += 1

    head = "".join(f'<th scope="col">{_inline(cell)}</th>' for cell in headers)
    body_rows = []
    for row in rows:
        if len(row) != len(headers):
            raise VerdictRenderError(
                f"table row has {len(row)} columns; expected {len(headers)}"
            )
        body_rows.append("<tr>" + "".join(f"<td>{_inline(cell)}</td>" for cell in row) + "</tr>")
    table = (
        '<div class="table-wrap" role="region" aria-label="Scrollable data table" tabindex="0">'
        f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table></div>"
    )
    return table, index


def _render_markdown(body: str) -> str:
    lines = body.splitlines()
    rendered: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("```"):
            language = stripped[3:].strip()
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].lstrip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index >= len(lines):
                raise VerdictRenderError("unterminated fenced code block")
            index += 1
            language_attr = f' class="language-{html.escape(language, quote=True)}"' if language else ""
            rendered.append(f"<pre><code{language_attr}>{html.escape(chr(10).join(code_lines), quote=True)}</code></pre>")
            continue
        if _is_table_start(lines, index):
            table, index = _render_table(lines, index)
            rendered.append(table)
            continue
        heading = re.match(r"^(#{3,6})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            rendered.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            index += 1
            continue
        unordered = re.match(r"^\s*[-*]\s+(.+)$", line)
        if unordered:
            items = []
            while index < len(lines):
                match = re.match(r"^\s*[-*]\s+(.+)$", lines[index])
                if not match:
                    break
                items.append(f"<li>{_inline(match.group(1))}</li>")
                index += 1
            rendered.append(f"<ul>{''.join(items)}</ul>")
            continue
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if ordered:
            items = []
            while index < len(lines):
                match = re.match(r"^\s*\d+[.)]\s+(.+)$", lines[index])
                if not match:
                    break
                items.append(f"<li>{_inline(match.group(1))}</li>")
                index += 1
            rendered.append(f"<ol>{''.join(items)}</ol>")
            continue

        paragraph = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip():
            if _is_table_start(lines, index) or re.match(r"^(?:#{3,6}\s+|\s*[-*]\s+|\s*\d+[.)]\s+|```)", lines[index]):
                break
            paragraph.append(lines[index].strip())
            index += 1
        rendered.append(f"<p>{_inline(' '.join(paragraph))}</p>")
    return "\n".join(rendered)


def _pattern_details(document: VerdictDocument) -> tuple[str, str]:
    recommendation = _section(document, "Recommended pattern")
    if recommendation is None:
        raise VerdictRenderError("recommended pattern section is unavailable")
    match = re.search(r"\b(?:\d{2}-[a-z0-9-]+|escape-hatch)\b", recommendation.body)
    if match is None:
        raise VerdictRenderError("recommended pattern has no canonical ID")
    pattern_id = match.group(0)
    if pattern_id == "escape-hatch":
        return pattern_id, "Escape hatch"
    pattern_path = _SKILL_DIR / "framework" / "patterns" / f"{pattern_id}.md"
    if not pattern_path.is_file():
        raise VerdictRenderError(f"pattern definition is missing: {pattern_id}")
    heading = _headings(pattern_path.read_text(encoding="utf-8"), 1)
    if not heading:
        raise VerdictRenderError(f"pattern definition has no title: {pattern_id}")
    pattern_name = re.sub(rf"^{re.escape(pattern_id[:2])}\s*[^A-Za-z0-9]+\s*", "", heading[0][0]).strip()
    return pattern_id, pattern_name


def _metric_card(value: str, label: str) -> str:
    accessible = html.escape(f"{value} {label}", quote=True)
    return f'<div class="metric" aria-label="{accessible}"><strong>{html.escape(value)}</strong><span>{html.escape(label)}</span></div>'


def render_html(document: VerdictDocument, metrics: SummaryMetrics, generated_on: date) -> str:
    """Render an offline, semantic Editorial Brief report."""

    pattern_id, pattern_name = _pattern_details(document)
    judgment_label = "judgment step" if metrics.judgment_steps == 1 else "judgment steps"
    cards = [_metric_card(str(metrics.judgment_steps), judgment_label)]
    cards.append(_metric_card(", ".join(metrics.tiers) or "None", "model tiers"))
    cards.append(_metric_card("Required" if metrics.human_gate else "Not required", "Human gate"))
    if metrics.audited_units is not None and metrics.unaudited_units is not None:
        cards.append(_metric_card(str(metrics.audited_units), "audited unit" if metrics.audited_units == 1 else "audited units"))
        cards.append(_metric_card(str(metrics.unaudited_units), "unaudited unit" if metrics.unaudited_units == 1 else "unaudited units"))

    sections = []
    for index, section in enumerate(document.sections, start=1):
        section_id = f"section-{index}-{_slugify(section.title)}"
        sections.append(
            f'<section class="brief-card" aria-labelledby="{section_id}">'
            f'<div class="section-number" aria-hidden="true">{index:02d}</div>'
            f'<div><h2 id="{section_id}">{html.escape(section.title, quote=True)}</h2>'
            f"{_render_markdown(section.body)}</div></section>"
        )

    css = """
:root { color-scheme: light; --ink:#27231f; --muted:#6e665d; --paper:#fbf7ef; --card:#fffdf8; --line:#ded4c6; --accent:#a84e32; --accent-soft:#f4ddd1; --green:#38634b; --green-soft:#deeee3; }
* { box-sizing:border-box; }
html { background:#e8e0d4; color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; line-height:1.6; }
body { margin:0; }
.page { width:min(1120px,calc(100% - 32px)); margin:32px auto; background:var(--paper); border:1px solid var(--line); box-shadow:0 20px 60px rgba(52,42,31,.12); }
.hero { padding:clamp(28px,6vw,72px); border-bottom:1px solid var(--line); background:linear-gradient(135deg,#fffaf0 0%,#f8eadf 100%); }
.eyebrow { color:var(--accent); font-size:.78rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
h1 { max-width:850px; margin:.35rem 0 1.25rem; font-family:Georgia,"Times New Roman",serif; font-size:clamp(2.25rem,7vw,5rem); line-height:1.02; letter-spacing:-.035em; }
.hero-meta { display:flex; flex-wrap:wrap; gap:10px; align-items:center; color:var(--muted); }
.badge { display:inline-flex; align-items:center; gap:.4rem; border-radius:999px; padding:.35rem .75rem; font-size:.84rem; font-weight:750; }
.verified { color:var(--green); background:var(--green-soft); }
.pattern { color:#74402e; background:var(--accent-soft); }
.metrics { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1px; background:var(--line); border-bottom:1px solid var(--line); }
.metric { min-height:115px; padding:24px; background:var(--card); }
.metric strong { display:block; font-family:Georgia,"Times New Roman",serif; font-size:1.7rem; line-height:1.15; }
.metric span { display:block; margin-top:.4rem; color:var(--muted); font-size:.82rem; text-transform:uppercase; letter-spacing:.06em; }
.content { padding:clamp(20px,5vw,64px); }
.brief-card { display:grid; grid-template-columns:52px minmax(0,1fr); gap:20px; padding:30px 0; border-top:1px solid var(--line); break-inside:avoid; }
.brief-card:first-child { border-top:0; padding-top:0; }
.section-number { color:var(--accent); font:700 .78rem/1.6 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.08em; }
h2,h3,h4 { line-height:1.25; }
h2 { margin:0 0 1rem; font-family:Georgia,"Times New Roman",serif; font-size:clamp(1.55rem,3vw,2.25rem); }
h3 { margin:1.6rem 0 .6rem; }
p,ul,ol,pre,.table-wrap { margin:0 0 1rem; }
code { border-radius:4px; padding:.12em .32em; background:#eee6da; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:.9em; }
pre { overflow:auto; padding:18px; border:1px solid var(--line); background:#25221f; color:#fffaf0; }
pre code { padding:0; background:transparent; color:inherit; }
.evidence { display:inline-block; border-radius:4px; padding:.05em .38em; font-size:.9em; font-weight:700; }
.assumption { color:#814027; background:#f7ddd1; }
.measurement { color:#315b46; background:#deeee3; }
.table-wrap { overflow-x:auto; border:1px solid var(--line); background:var(--card); }
.table-wrap:focus { outline:3px solid rgba(168,78,50,.35); outline-offset:2px; }
table { width:100%; border-collapse:collapse; min-width:620px; font-size:.92rem; }
th,td { padding:12px 14px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:#554c43; background:#f3ece1; font-size:.78rem; letter-spacing:.04em; text-transform:uppercase; }
tbody tr:last-child td { border-bottom:0; }
@media (max-width: 640px) { .page { width:100%; margin:0; border:0; } .hero { padding:28px 20px; } .content { padding:24px 20px; } .brief-card { grid-template-columns:minmax(0,1fr); gap:4px; } .metric { min-height:96px; padding:18px 20px; } }
@media print { html { background:#fff; } .page { width:100%; margin:0; border:0; box-shadow:none; } .hero { padding:24px 0; background:#fff; } .content { padding:20px 0; } .brief-card { break-inside:avoid; } .table-wrap { overflow:visible; } table { min-width:0; } }
""".strip()

    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(document.title, quote=True)} - Architecture verdict</title>"
        f"<style>{css}</style></head><body><main class=\"page\">"
        f'<header class="hero"><div class="eyebrow">Architecture Editorial Brief</div><h1>{html.escape(document.title, quote=True)}</h1>'
        f'<div class="hero-meta"><span class="badge verified">Structure checked</span><span class="badge pattern">{html.escape(pattern_name)} <code>{html.escape(pattern_id)}</code></span>'
        f'<time datetime="{generated_on.isoformat()}">{generated_on.isoformat()}</time></div>'
        '<p>Automated checks cover report structure and selected consistency rules. '
        'A pass does not establish that the recommendation is correct or safe to implement.</p></header>'
        f'<section class="metrics" aria-label="Verdict summary">{"".join(cards)}</section>'
        f'<div class="content">{"".join(sections)}</div></main></body></html>\n'
    )


class _OutputContractParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.script_count = 0
        self.remote_attributes: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            self.script_count += 1
        for name, value in attrs:
            if name.lower() in {"src", "href", "action"} and value and value.lower().startswith(("http://", "https://", "//", "javascript:")):
                self.remote_attributes.append((tag, name, value))


def _validate_html(output: str, document: VerdictDocument) -> None:
    required = ("<!doctype html>", '<meta charset="utf-8">', "<main", "<style>", "@media print", "Structure checked")
    missing = [token for token in required if token not in output]
    if missing:
        raise VerdictRenderError(f"rendered HTML is missing required output: {', '.join(missing)}")
    parser = _OutputContractParser()
    parser.feed(output)
    if parser.script_count or parser.remote_attributes:
        raise VerdictRenderError("rendered HTML contains active or remote content")
    for section in document.sections:
        if html.escape(section.title, quote=True) not in output:
            raise VerdictRenderError(f"rendered HTML omitted section: {section.title}")


def render_file(source: Path, destination: Path, generated_on: date | None = None) -> Path:
    """Validate and atomically render one Markdown verdict to HTML."""

    source = Path(source)
    destination = Path(destination)
    violations = check_verdict(source)
    if violations:
        details = "; ".join(str(violation) for violation in violations)
        raise VerdictRenderError(f"verdict validation failed: {details}")

    document = parse_verdict(source.read_text(encoding="utf-8"))
    output = render_html(document, derive_metrics(document), generated_on or date.today())
    _validate_html(output, document)

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(output)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: python render_verdict.py SOURCE.md OUTPUT.html", file=sys.stderr)
        return 2
    try:
        render_file(Path(args[0]), Path(args[1]))
    except (OSError, UnicodeError, VerdictRenderError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
