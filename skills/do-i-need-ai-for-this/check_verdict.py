"""Check a produced verdict document for structural and content defects.

Standalone implementation — stdlib-only, no external dependencies.
Run from the skill directory:

    python check_verdict.py <path-to-verdict.md>

Section names, valid pattern IDs, and the model-tier names are derived at import
time from the framework files that live alongside this module, so the checker
cannot drift from the framework it enforces.

Exits 0 when the document is clean, 1 when violations are found.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Skill directory: this file lives in skills/do-i-need-ai-for-this/
_SKILL_DIR = Path(__file__).resolve().parent
_FRAMEWORK_DIR = _SKILL_DIR / "framework"
_TEMPLATE_PATH = _FRAMEWORK_DIR / "verdict-template.md"
_PATTERNS_DIR = _FRAMEWORK_DIR / "patterns"
_TIERS_PATH = _FRAMEWORK_DIR / "model-tiers.md"
_ESCAPE_HATCH_ID = "escape-hatch"

# Heading markers for template sections that only some verdicts carry. A section
# marked this way is not required of every verdict, so it is excluded from the
# canonical section list rather than failing every verdict that omits it.
_OPTIONAL_SECTION_MARKERS = (
    "audit entry point only",
    "multi-unit audits only",
)

# Level-2 sections of a multi-unit audit, matched by slug prefix because verdicts
# in the field drop the parenthetical marker the template carries.
_INVENTORY_SLUG = "inventory"
_UNIT_VERDICTS_SLUG = "unit-verdicts"
_NOT_AUDITED_SLUG = "not-audited"

# Inventory table columns the checker reads. Everything else in the table is for
# the reader, so an auditor can add columns without breaking the gate.
_UNIT_COLUMN = "unit"
_AUDITED_COLUMN = "audited"
_AUDITED_YES = "yes"
_AUDITED_NO = "no"

# A not-audited entry must give a reason, not just name the unit. Ten characters
# past the unit name is not a quality bar; it distinguishes a reason from a bare
# list item, which is the failure this catches.
_MIN_REASON_CHARS = 10

# Matches [measured: ...] or [assumed: ...] labels in table cells
_LABEL_RE = re.compile(r"\[(measured|assumed):[^\]]*\]", re.IGNORECASE)

# Matches [measured: <source>] to extract the source text
_MEASURED_RE = re.compile(r"\[measured:([^\]]*)\]", re.IGNORECASE)

# Words that reveal a "measured" label is actually an estimate or derivation
_LAUNDERING_RE = re.compile(r"\b(assum|estimat|derived|typical)\w*", re.IGNORECASE)

# Separator rows consist only of pipes, dashes, colons, and whitespace
_SEPARATOR_ROW_RE = re.compile(r"^[-|:\s]+$")

# Keywords that indicate a build recommendation is being made
_BUILD_REC_RE = re.compile(r"\b(build|implement|proceed|recommend)\b", re.IGNORECASE)

# Required pattern-04 contract fields. Each value must remain on the same line so
# the contract is both skimmable by a reviewer and deterministic to check.
_VERIFIER_CONTRACT_FIELDS = {
    "proves": re.compile(
        r"^\s*-\s+\*\*Verifier proves:\*\*\s*(\S.*)$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "does-not-prove": re.compile(
        r"^\s*-\s+\*\*Verifier does not prove:\*\*\s*(\S.*)$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "post-pass-gate": re.compile(
        r"^\s*-\s+\*\*Post-pass gate:\*\*\s*(\S.*)$",
        re.IGNORECASE | re.MULTILINE,
    ),
}
_NONE_WITH_BASIS_RE = re.compile(
    r"^none\s*\[basis:\s*\S.{2,}\]\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Violation:
    """A structural defect found in a verdict document."""

    check: str
    path: str
    message: str

    def __str__(self) -> str:
        """Format as 'check: path: message'."""
        return f"{self.check}: {self.path}: {self.message}"


def _slugify(text: str) -> str:
    """Return a lowercase, hyphen-separated slug with no non-alphanumeric characters."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return slug.strip("-")


def _headings(text: str, level: int) -> list[tuple[str, int]]:
    """Return (title, line_index) pairs for every heading at exactly level.

    Code-fenced blocks (delimited by ``` markers) are excluded so that a
    ``#``-prefixed line inside an example is not parsed as a heading.
    """
    marker = "#" * level + " "
    out: list[tuple[str, int]] = []
    fence_open = False
    for index, line in enumerate(text.splitlines()):
        if line.lstrip().startswith("```"):
            fence_open = not fence_open
            continue
        if fence_open:
            continue
        if line.startswith(marker):
            out.append((line[len(marker) :].strip(), index))
    return out


def _sections(text: str, level: int) -> dict[str, str]:
    """Map each slugified heading to its body text for headings at the given level."""
    lines = text.splitlines()
    headings = _headings(text, level)
    out: dict[str, str] = {}
    for idx, (title, start) in enumerate(headings):
        end = headings[idx + 1][1] if idx + 1 < len(headings) else len(lines)
        out[_slugify(title)] = "\n".join(lines[start + 1 : end])
    return out


def _load_verdict_sections() -> tuple[str, ...]:
    """Parse expected section names from the template, excluding optional sections.

    Reads framework/verdict-template.md and returns the slugified names of all
    level-2 headings that carry none of ``_OPTIONAL_SECTION_MARKERS``. Without
    the exclusion, adding a section that only audit mode or only a multi-unit
    audit produces would fail every verdict that correctly omits it.
    """
    text = _TEMPLATE_PATH.read_text(encoding="utf-8")
    return tuple(
        _slugify(title)
        for title, _ in _headings(text, level=2)
        if not any(marker in title.lower() for marker in _OPTIONAL_SECTION_MARKERS)
    )


def _load_pattern_ids() -> tuple[str, ...]:
    """Derive valid pattern IDs from pattern filenames in framework/patterns/.

    Returns the sorted stems of all *.md files in the patterns directory,
    excluding README.md.
    """
    if not _PATTERNS_DIR.exists():
        return ()
    return tuple(
        sorted(p.stem for p in _PATTERNS_DIR.glob("*.md") if p.name != "README.md")
    )


def _load_tier_names() -> tuple[str, ...]:
    """Derive the model-tier names from the level-2 headings of model-tiers.md.

    Tier headings are written in capitals and prose headings are not — the same
    convention labeling.md uses for DETERMINISTIC, JUDGMENT and HUMAN — so the
    names are read out of the framework file rather than restated here, where a
    rename would leave the checker enforcing a vocabulary the framework no
    longer uses.
    """
    if not _TIERS_PATH.exists():
        return ()
    text = _TIERS_PATH.read_text(encoding="utf-8")
    return tuple(title for title, _ in _headings(text, level=2) if title.isupper())


# Constants derived from the framework files at import time so the checker
# cannot drift from the framework it enforces.
VERDICT_SECTIONS: tuple[str, ...] = _load_verdict_sections()
PATTERN_IDS: tuple[str, ...] = _load_pattern_ids()
TIER_NAMES: tuple[str, ...] = _load_tier_names()

# A tier counts only in capitals, the way the step labels are written. Matching
# case-insensitively would let a step described as "the strongest signal in the
# log" satisfy the rule by accident, which is worse than not checking: the row
# would read as tiered to the gate and untiered to a person. The trailing
# ``[A-Z]*`` accepts STRONGEST and WEAKEST, which is how the tiers get written
# in running prose.
_TIER_RE = (
    re.compile(r"\b(?:" + "|".join(TIER_NAMES) + r")[A-Z]*\b") if TIER_NAMES else None
)

_JUDGMENT_RE = re.compile(r"\bJUDGMENT\b")

# Content-consistency checks are intentionally narrow. They catch claims that
# contradict text in the same verdict; they do not attempt to decide whether
# the architecture itself is good.
_VISIBLE_CORRECTION_RE = re.compile(
    r"\b(?:wait\b[^.\n]{0,30})?(?:recalculat(?:e|ed|ing)|scratch that)\b",
    re.IGNORECASE,
)
_ON_PREM_RE = re.compile(
    r"\b(?:on[- ]prem(?:ises)?|no external cloud|must (?:remain|run) local(?:ly)?|"
    r"locally hosted)\b",
    re.IGNORECASE,
)
_EXTERNAL_MODEL_RE = re.compile(
    r"\b(?:claude|chatgpt|gpt[- ]?\d|gemini|azure openai|amazon bedrock)\b",
    re.IGNORECASE,
)
_OPTIONAL_AI_REVIEW_RE = re.compile(
    r"\b(?:human\s+or\s+(?:a\s+)?(?:separate\s+)?(?:ai|model)|"
    r"or\s+(?:a\s+)?(?:separate\s+)?(?:ai|model)\s+review)\b",
    re.IGNORECASE,
)
_NUMBER_TOKEN = r"~?\d[\d,]*(?:\.\d+)?\s*[kKmM]?"
_MULTIPLICATION_RE = re.compile(
    rf"(?P<a>{_NUMBER_TOKEN})[^0-9×*|\n]{{0,30}}[×*]\s*"
    rf"(?P<b>{_NUMBER_TOKEN})[^0-9×*|\n]{{0,30}}[×*]\s*\(?\s*"
    rf"(?P<c>{_NUMBER_TOKEN})\s*\+\s*(?P<d>{_NUMBER_TOKEN})",
)
_NUMBER_RE = re.compile(_NUMBER_TOKEN)


def _is_data_table_row(line: str) -> bool:
    """Return True if line is a Markdown table data row, not a separator row."""
    stripped = line.strip()
    return (
        bool(stripped) and stripped[0] == "|" and not _SEPARATOR_ROW_RE.match(stripped)
    )


def _split_table_cells(line: str) -> list[str]:
    """Split a Markdown table row on pipes outside inline-code spans."""
    stripped = line.strip().strip("|")
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    for char in stripped:
        if char == "`":
            in_code = not in_code
            current.append(char)
        elif char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def check_structure(text: str, path: str) -> list[Violation]:
    """Verify the canonical sections are present in order; extra sections are allowed."""
    found = [_slugify(title) for title, _ in _headings(text, level=2)]
    violations = [
        Violation("structure", path, f"missing section: {section}")
        for section in VERDICT_SECTIONS
        if section not in found
    ]
    if not violations:
        verdict_set = set(VERDICT_SECTIONS)
        ordered = [slug for slug in found if slug in verdict_set]
        if tuple(ordered) != VERDICT_SECTIONS:
            violations.append(
                Violation("structure", path, f"sections are out of order: {ordered}")
            )
    sections = _sections(text, level=2)
    violations.extend(
        Violation("structure", path, f"empty section: {section}")
        for section in VERDICT_SECTIONS
        if section in sections and not sections[section].strip()
    )
    return violations


def check_judgment_tiers(text: str, path: str) -> list[Violation]:
    """Verify every JUDGMENT row in the decomposition names a model tier.

    A JUDGMENT label says the step needs a model; the tier says which one. A row
    that answers only the first leaves the most expensive assumption in the
    design unstated — the strongest model available, chosen by default and never
    revisited — which is the error this whole framework exists to catch, one
    level down.

    Scoped to table rows in the Decomposition section, because that is where the
    labels are structured. A prose decomposition is not scanned, and neither are
    the condensed unit verdicts, where JUDGMENT appears in running text and
    requiring a tier token nearby would reject correct sentences for their word
    order. The tier may sit in any cell of the row: the template gives it a
    column, but a reason cell reading "MID — three sources to reconcile" is the
    same claim, and rejecting it would fail rows for their layout rather than
    for their content.
    """
    if _TIER_RE is None:
        return []
    body = _sections(text, level=2).get("decomposition", "")
    return [
        Violation(
            "model-tier",
            path,
            "decomposition: JUDGMENT step names no model tier"
            f" (expected one of: {', '.join(TIER_NAMES)}): {line.strip()!r}",
        )
        for line in body.splitlines()
        if _is_data_table_row(line)
        and _JUDGMENT_RE.search(line)
        and not _TIER_RE.search(line)
    ]


def check_pattern_validity(text: str, path: str) -> list[Violation]:
    """Verify the recommended pattern is a canonical pattern ID or the escape hatch."""
    sec = _sections(text, level=2)
    rec = sec.get("recommended-pattern", "")
    valid_ids = set(PATTERN_IDS) | {_ESCAPE_HATCH_ID}
    if not any(pid in rec for pid in valid_ids):
        return [
            Violation(
                "pattern-validity",
                path,
                "recommended-pattern section names no canonical pattern ID"
                f" (expected one of: {', '.join(sorted(valid_ids))})",
            )
        ]
    return []


def _contract_value(pattern: re.Pattern[str], body: str) -> str | None:
    """Return a normalized one-line verifier-contract value when present."""
    match = pattern.search(body)
    if match is None:
        return None
    return match.group(1).strip().strip("`").strip()


def check_verifier_boundary(text: str, path: str) -> list[Violation]:
    """Enforce the proof boundary and post-pass gate for pattern 04 verdicts."""
    sections = _sections(text, level=2)
    recommendation = sections.get("recommended-pattern", "")
    if "04-generate-then-verify" not in recommendation:
        return []

    values = {
        name: _contract_value(pattern, recommendation)
        for name, pattern in _VERIFIER_CONTRACT_FIELDS.items()
    }
    violations = [
        Violation(
            "verifier-boundary",
            path,
            f"pattern 04 recommendation is missing verifier contract field: {name}",
        )
        for name, value in values.items()
        if value is None
    ]
    if violations:
        return violations

    proves = values["proves"] or ""
    gap = values["does-not-prove"] or ""
    gate = values["post-pass-gate"] or ""
    if not proves:
        violations.append(
            Violation(
                "verifier-boundary",
                path,
                "Verifier proves field must name the deterministic property established",
            )
        )

    gap_is_none = gap.lower().startswith("none")
    if gap_is_none and not _NONE_WITH_BASIS_RE.fullmatch(gap):
        violations.append(
            Violation(
                "verifier-boundary",
                path,
                "Verifier does not prove may say none only as"
                " 'none [basis: <deterministic evidence>]'",
            )
        )

    gate_lower = gate.lower()
    is_automatic = gate_lower.startswith("automatic")
    is_human = gate_lower.startswith("human")
    if not is_automatic and not is_human:
        violations.append(
            Violation(
                "verifier-boundary",
                path,
                "Post-pass gate must start with AUTOMATIC or HUMAN",
            )
        )
    if not gap_is_none and not is_human:
        violations.append(
            Violation(
                "verifier-boundary",
                path,
                "pattern 04 cannot auto-act while the verifier leaves a named gap;"
                " use a HUMAN post-pass gate",
            )
        )
    if is_human:
        if "every generated candidate" not in gate_lower or "approv" not in gate_lower:
            violations.append(
                Violation(
                    "verifier-boundary",
                    path,
                    "HUMAN post-pass gate must state that every generated candidate"
                    " requires approval",
                )
            )
        decomposition = sections.get("decomposition", "")
        if not re.search(r"\bHUMAN\b", decomposition):
            violations.append(
                Violation(
                    "verifier-boundary",
                    path,
                    "HUMAN post-pass gate is not represented in the decomposition",
                )
            )
    return violations


def check_figure_labelling(text: str, path: str) -> list[Violation]:
    """Verify each numeric value cell carries its own measured or assumed label."""
    sec = _sections(text, level=2)
    cost = sec.get("cost-comparison", "")
    violations: list[Violation] = []
    for line in cost.splitlines():
        if not _is_data_table_row(line):
            continue
        for cell in _split_table_cells(line)[1:]:
            if re.search(r"\d", cell) and not _LABEL_RE.search(cell):
                violations.append(
                    Violation(
                        "figure-labelling",
                        path,
                        "cost-comparison: numeric value has no [measured:] or [assumed:]"
                        f" label in cell: {cell!r}",
                    )
                )
    return violations


def check_rerunnable_sources(text: str, path: str) -> list[Violation]:
    """Verify every [measured:] label names a re-runnable source, not an assumption.

    Scoped to the cost comparison, where measured labels are load-bearing and
    where ``check_figure_labelling`` requires them. Scanning the whole document
    could not tell a label being *used* from one being *mentioned*, so a verdict
    that discussed this rule failed it — a real audit of this repository was
    rejected for the sentence explaining what the rule does. A checker that
    cannot survive being described is one nobody can write about accurately.
    """
    sec = _sections(text, level=2)
    cost = sec.get("cost-comparison", "")
    violations: list[Violation] = []
    for match in _MEASURED_RE.finditer(cost):
        source = match.group(1)
        if _LAUNDERING_RE.search(source):
            violations.append(
                Violation(
                    "rerunnable-sources",
                    path,
                    "measured label contains laundering word"
                    f" (assum/estimat/derived/typical): {match.group(0)!r}",
                )
            )
        elif "`" not in source:
            violations.append(
                Violation(
                    "rerunnable-sources",
                    path,
                    "measured label must contain a re-runnable command or query in backticks:"
                    f" {match.group(0)!r}",
                )
            )
    return violations


def check_agent_loop_addressed(text: str, path: str) -> list[Violation]:
    """Verify the rejected-alternatives section mentions the agent loop."""
    sec = _sections(text, level=2)
    body = sec.get("rejected-alternatives", "").lower()
    if "agent loop" not in body and "agent-loop" not in body:
        return [
            Violation(
                "agent-loop",
                path,
                "rejected-alternatives section does not mention the agent loop",
            )
        ]
    return []


def check_deciding_figure_disclosure(text: str, path: str) -> list[Violation]:
    """Verify a build recommendation with assumed figures acknowledges the assumption."""
    sec = _sections(text, level=2)
    rec = sec.get("recommended-pattern", "")
    if not _BUILD_REC_RE.search(rec):
        return []
    if not re.search(r"\[assumed:", text, re.IGNORECASE):
        return []
    if "assumed" not in rec.lower():
        return [
            Violation(
                "deciding-figure",
                path,
                "recommended-pattern section makes a build recommendation but does not"
                " acknowledge that a figure is assumed",
            )
        ]
    return []


def _number_value(token: str) -> float | None:
    """Return a compact human number such as ``~1.5M`` as a float."""
    raw = token.strip().lstrip("~").replace(",", "").replace(" ", "")
    multiplier = 1.0
    if raw[-1:].lower() == "k":
        raw, multiplier = raw[:-1], 1_000.0
    elif raw[-1:].lower() == "m":
        raw, multiplier = raw[:-1], 1_000_000.0
    try:
        return float(raw) * multiplier
    except ValueError:
        return None


def _model_cells(body: str) -> list[str]:
    """Return model-name cells from a model-placement Markdown table."""
    rows = [
        _split_table_cells(line)
        for line in body.splitlines()
        if _is_data_table_row(line)
    ]
    if not rows:
        return []
    headers = [_slugify(cell) for cell in rows[0]]
    try:
        model_at = next(
            index
            for index, header in enumerate(headers)
            if header in {"model", "model-today", "example-model"}
        )
    except StopIteration:
        return []
    return [row[model_at] for row in rows[1:] if len(row) > model_at]


def check_content_consistency(text: str, path: str) -> list[Violation]:
    """Reject explicit contradictions and exposed working in a verdict.

    This is a consistency gate, not a correctness oracle. It checks only facts
    the document supplies enough information to compare deterministically:
    arithmetic written beside its claimed total, constraints against example
    model names, and labels against alternatives named in the same row.
    """
    sections = _sections(text, level=2)
    cost = sections.get("cost-comparison", "")
    placement = sections.get("model-placement", "")
    decomposition = sections.get("decomposition", "")
    violations: list[Violation] = []

    if _VISIBLE_CORRECTION_RE.search(cost):
        violations.append(
            Violation(
                "content-consistency",
                path,
                "cost comparison exposes a self-correction; replace it with one"
                " reconciled figure",
            )
        )

    for line in cost.splitlines():
        if not _is_data_table_row(line):
            continue
        for cell in _split_table_cells(line)[1:]:
            expression = _MULTIPLICATION_RE.search(cell)
            if expression is None:
                continue
            declared_match = _NUMBER_RE.search(cell[: expression.start()])
            if declared_match is None:
                continue
            declared = _number_value(declared_match.group(0))
            factors = [
                _number_value(expression.group(name)) for name in ("a", "b", "c", "d")
            ]
            if declared in (None, 0) or any(value is None for value in factors):
                continue
            a, b, c, d = factors
            calculated = a * b * (c + d)
            ratio = max(declared, calculated) / min(declared, calculated)
            # Order-of-magnitude figures may differ by normal rounding. Five
            # times apart is not rounding; it changes the cost conclusion.
            if ratio >= 5:
                violations.append(
                    Violation(
                        "content-consistency",
                        path,
                        "cost cell's stated total disagrees with its written"
                        f" multiplication by {ratio:.1f}x: {cell!r}",
                    )
                )

    frame = sections.get("frame", "")
    if _ON_PREM_RE.search(frame):
        incompatible = [
            model
            for model in _model_cells(placement)
            if _EXTERNAL_MODEL_RE.search(model)
        ]
        if incompatible:
            violations.append(
                Violation(
                    "constraint-consistency",
                    path,
                    "model placement names an external hosted model despite an"
                    f" on-premises constraint: {', '.join(incompatible)}",
                )
            )

    for line in decomposition.splitlines():
        if (
            _is_data_table_row(line)
            and re.search(r"\bHUMAN\b", line)
            and _OPTIONAL_AI_REVIEW_RE.search(line)
        ):
            violations.append(
                Violation(
                    "human-boundary",
                    path,
                    "a HUMAN row also permits AI review; split the alternatives or"
                    f" label the mandatory path accurately: {line.strip()!r}",
                )
            )
    return violations


def _optional_section(sections: dict[str, str], slug: str) -> str | None:
    """Return the body of an optional section named *slug*, or None.

    Matches the bare slug and the slug carrying its template marker, because
    the template heading reads "Inventory (multi-unit audits only)" while
    verdicts in the field write "Inventory". Both must resolve to the same
    section or the gate would depend on whether the author copied the
    parenthetical.
    """
    for key, body in sections.items():
        if key == slug or key.startswith(slug + "-"):
            return body
    return None


def _mentions_unit(text: str, unit: str) -> bool:
    """Return True when *text* names *unit* at token boundaries.

    Both sides are slugified so that ``rtl_agent``, `` `rtl_agent` `` and
    "RTL agent" all match one inventory row. The boundaries stop ``rtl`` from
    matching ``rtl_agent``; they do not stop ``rtl_agent`` from matching
    ``rtl_agent_v2``, which is what :func:`_units_named` resolves.
    """
    unit_slug = _slugify(unit)
    if not unit_slug:
        return False
    return (
        re.search(rf"(?:^|-){re.escape(unit_slug)}(?:-|$)", _slugify(text)) is not None
    )


def _units_named(text: str, units: list[str]) -> set[str]:
    """Return the inventoried units *text* names, keeping only the longest match.

    ``uarch-setup`` is a token prefix of ``uarch-setup-simulate``, so a line
    naming the second also matches the first. Discarding any match contained in
    a longer one stops a unit from being accounted for by its own sibling's row,
    which would silently satisfy the reconciliation this check exists to enforce.
    """
    matched = {unit for unit in units if _mentions_unit(text, unit)}
    return {
        unit
        for unit in matched
        if not any(
            other != unit and _slugify(unit) in _slugify(other) for other in matched
        )
    }


def _parse_inventory(body: str) -> tuple[list[tuple[str, str]], bool]:
    """Return (unit, audited-flag) pairs from the inventory table, and whether one was found.

    The header row is located by name rather than by position so that an
    auditor may add, drop, or reorder the columns meant for the reader without
    changing what the checker reads.
    """
    columns: tuple[int, int] | None = None
    rows: list[tuple[str, str]] = []
    for line in body.splitlines():
        if not _is_data_table_row(line):
            continue
        cells = _split_table_cells(line)
        lowered = [cell.strip().lower() for cell in cells]
        if columns is None:
            if _UNIT_COLUMN in lowered and _AUDITED_COLUMN in lowered:
                columns = (
                    lowered.index(_UNIT_COLUMN),
                    lowered.index(_AUDITED_COLUMN),
                )
            continue
        unit_col, audited_col = columns
        if len(cells) <= max(unit_col, audited_col):
            continue
        unit = cells[unit_col].strip().strip("`").strip()
        if unit:
            rows.append((unit, cells[audited_col].strip().lower()))
    return rows, columns is not None


def _not_audited_entries(inventory_body: str) -> list[str]:
    """Return the list items of the not-audited section, empty when there is none.

    Only list items and table rows count as entries. A closing paragraph is
    ordinary prose, and counting its sentences as entries would reject a
    correctly written section for explaining itself.
    """
    block = _optional_section(_sections(inventory_body, level=3), _NOT_AUDITED_SLUG)
    if block is None:
        return []
    return [
        line
        for line in block.splitlines()
        if line.strip().startswith(("-", "*", "|"))
        and not _SEPARATOR_ROW_RE.match(line.strip())
    ]


def _reason_length(line: str, unit: str) -> int:
    """Return how many characters of *line* remain once the unit name and markup go."""
    remainder = re.sub(re.escape(unit), "", line, flags=re.IGNORECASE)
    return len(re.sub(r"[^0-9A-Za-z]+", "", remainder))


def check_unit_accounting(text: str, path: str) -> list[Violation]:
    """Verify a multi-unit audit accounts for every unit it inventoried.

    Every inventory row must appear exactly once as a unit verdict or once in
    the not-audited list, and nothing may appear in either place that the
    inventory does not list. This is the check that makes the coverage claim
    structural: a verdict that inventories twenty-seven units, audits six and
    stays silent on the rest reads as a verdict on the whole target, and no
    amount of prose discipline reliably prevents that.
    """
    sections = _sections(text, level=2)
    inventory = _optional_section(sections, _INVENTORY_SLUG)
    unit_verdicts = _optional_section(sections, _UNIT_VERDICTS_SLUG)
    if inventory is None:
        if unit_verdicts is None:
            return []  # a single-unit verdict; nothing to reconcile
        return [
            Violation(
                "unit-accounting",
                path,
                "unit verdicts are present with no inventory section to reconcile"
                " them against",
            )
        ]

    rows, table_found = _parse_inventory(inventory)
    if not table_found:
        return [
            Violation(
                "unit-accounting",
                path,
                "inventory section has no table with"
                f" '{_UNIT_COLUMN}' and '{_AUDITED_COLUMN}' columns",
            )
        ]
    if not rows:
        return [Violation("unit-accounting", path, "inventory table lists no units")]

    inventoried = [unit for unit, _ in rows]
    verdict_headings = [
        (title, _units_named(title, inventoried))
        for title, _ in _headings(unit_verdicts or "", level=3)
    ]
    skipped = [
        (line, _units_named(line, inventoried))
        for line in _not_audited_entries(inventory)
    ]
    violations: list[Violation] = []
    accounted_audited = 0
    accounted_skipped = 0

    for unit, flag in rows:
        has_verdict = any(unit in named for _, named in verdict_headings)
        skip_lines = [line for line, named in skipped if unit in named]
        if flag not in (_AUDITED_YES, _AUDITED_NO):
            violations.append(
                Violation(
                    "unit-accounting",
                    path,
                    f"inventory unit {unit!r} has audited={flag!r};"
                    f" expected {_AUDITED_YES!r} or {_AUDITED_NO!r}",
                )
            )
        if has_verdict and skip_lines:
            violations.append(
                Violation(
                    "unit-accounting",
                    path,
                    f"inventory unit {unit!r} appears both as a unit verdict and in"
                    " the not-audited list",
                )
            )
        elif has_verdict:
            accounted_audited += 1
            if flag == _AUDITED_NO:
                violations.append(
                    Violation(
                        "unit-accounting",
                        path,
                        f"inventory unit {unit!r} is marked not audited but has a"
                        " unit verdict",
                    )
                )
        elif skip_lines:
            accounted_skipped += 1
            if flag == _AUDITED_YES:
                violations.append(
                    Violation(
                        "unit-accounting",
                        path,
                        f"inventory unit {unit!r} is marked audited but appears in"
                        " the not-audited list",
                    )
                )
            if all(
                _reason_length(line, unit) < _MIN_REASON_CHARS for line in skip_lines
            ):
                violations.append(
                    Violation(
                        "unit-accounting",
                        path,
                        f"not-audited entry for {unit!r} names no reason",
                    )
                )
        else:
            violations.append(
                Violation(
                    "unit-accounting",
                    path,
                    f"inventory unit {unit!r} has neither a unit verdict nor a"
                    " not-audited entry",
                )
            )

    for title, named in verdict_headings:
        if not named:
            violations.append(
                Violation(
                    "unit-accounting",
                    path,
                    f"unit verdict {title!r} names no unit in the inventory table",
                )
            )
    for line, named in skipped:
        if not named:
            violations.append(
                Violation(
                    "unit-accounting",
                    path,
                    f"not-audited entry {line.strip()!r} names no unit in the"
                    " inventory table",
                )
            )

    total = accounted_audited + accounted_skipped
    if total != len(rows):
        violations.append(
            Violation(
                "unit-accounting",
                path,
                f"counts do not reconcile: {len(rows)} units inventoried,"
                f" {accounted_audited} with a unit verdict,"
                f" {accounted_skipped} in the not-audited list",
            )
        )
    return violations


def check_unit_pattern_validity(text: str, path: str) -> list[Violation]:
    """Verify every unit verdict names a canonical pattern ID or the escape hatch.

    Reported under the same check name as the system-level rule because it is
    the same rule at a smaller scope: a per-unit recommendation that names no
    catalog entry is a label the reader cannot look up.
    """
    unit_verdicts = _optional_section(_sections(text, level=2), _UNIT_VERDICTS_SLUG)
    if unit_verdicts is None:
        return []
    valid_ids = set(PATTERN_IDS) | {_ESCAPE_HATCH_ID}
    bodies = _sections(unit_verdicts, level=3)
    return [
        Violation(
            "pattern-validity",
            path,
            f"unit verdict {title!r} names no canonical pattern ID"
            f" (expected one of: {', '.join(sorted(valid_ids))})",
        )
        for title, _ in _headings(unit_verdicts, level=3)
        if not any(pid in bodies.get(_slugify(title), "") for pid in valid_ids)
    ]


_ALL_CHECKS = (
    check_structure,
    check_judgment_tiers,
    check_pattern_validity,
    check_verifier_boundary,
    check_agent_loop_addressed,
    check_content_consistency,
    check_unit_accounting,
    check_unit_pattern_validity,
)


def check_verdict(path: Path) -> list[Violation]:
    """Run all checks against the verdict document at path."""
    text = path.read_text(encoding="utf-8")
    rel = str(path)
    return [v for checker in _ALL_CHECKS for v in checker(text, rel)]


def main(argv: list[str] | None = None) -> int:
    """Check a produced verdict document for structural and content defects.

    Usage: python check_verdict.py <path-to-verdict.md>
    Returns 0 if clean, 1 if violations found.
    """
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("usage: python check_verdict.py <path-to-verdict.md>")
        return 1
    path = Path(argv[0])
    if not path.exists():
        print(f"error: {path} does not exist")
        return 1
    violations = check_verdict(path)
    count = len(violations)
    for violation in violations:
        print(f"{violation.check}: {violation.path}: {violation.message}")
    print(f"{count} violation(s)")
    return 0 if count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
