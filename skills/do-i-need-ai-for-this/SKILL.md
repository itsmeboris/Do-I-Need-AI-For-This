---
name: do-i-need-ai-for-this
description: Use when deciding how to implement an automation task, spec, or idea, or when reviewing an existing agent or script for wasted model invocations. Produces an architecture verdict placing judgment only where it is irreducible.
---

# do-i-need-ai-for-this

Announce: "Using do-i-need-ai-for-this to produce an architecture verdict."

## Entry point

Pick the entry point. Use `verdict` for an idea or spec; `audit` for an existing
implementation, script, prompt, or repository. If the user's request is ambiguous,
ask once before continuing.

## Input boundary

Use only material already available in the active environment: pasted text,
uploaded files, files selected for a Cowork task, or the current local workspace.
Do not clone, fetch, or authenticate to obtain more material. When an audit target
is unavailable, name what is missing and ask the user to paste, upload, or select
it. Never infer conclusions about files that were not available for review.

## Step 1 — Screen the input

Read `framework/antipatterns.md`. Scan the input for any phrase matches and record
them as flags. Do not raise flags as criticism; carry them forward to the verdict
frame section.

## Step 2 — Inventory the target (audit only)

Skip this step for the `verdict` entry point. For `audit`, read
`framework/inventory.md` and enumerate the units in the target before filling any
frame. Count the distinct (trigger, blast radius) pairs.

One pair: continue at step 3 and produce an ordinary single-unit verdict.

More than one: rank the units by model spend × blast radius, then show the user
the ranked inventory and the depth you intend — the top five to eight — in the
same message that confirms the frame. Depth is theirs to set, and it is cheap to
ask before the expensive part rather than after. Steps 3 through 5 then run once
per audited unit and once for the system as a whole; the system-level pass treats
dispatch and re-dispatch as its own automation, because they are.

Every unit you inventory must end up either as a unit verdict or in the
not-audited list with its reason. A verdict that overstates its own coverage is
worse than no verdict, and step 8 fails the gate on it.

## Step 3 — Fill the frame

Read `framework/frame.md`, then `framework/questions.md`. Parse the user's existing
description into slots first, and never ask for something the user has already
stated.

Then ask. An assumption is not a shortcut, it is a place the verdict can be wrong
without anyone noticing. Ask whenever a slot is unstated and its value would change
the recommendation -- at most three questions per message, each answerable in a
sentence. These four decide which pattern wins, so prefer asking over assuming:

- **Cadence and volume** -- whether building it repays the effort at all (`01-dont-build-it`)
- **Action and blast radius** -- whether a person must authorize the action (`06-propose-and-approve`)
- **Tolerance and review** -- how much the design must defend against being wrong
- **Success signal** -- without one, no failure mode is detectable

Classify every unresolved slot before proceeding:

- **Decision-changing** -- its answer could change pattern selection, model
  placement, the build-vs-don't-build decision, a safety gate, or feasibility.
- **Low-impact** -- its answer changes implementation detail but cannot change the
  verdict.

After every answer round, re-evaluate the frame. If decision-changing unknowns
remain, ask one additional question round, again capped at three questions. If
they remain unanswered because the user does not know, or the user asks to move
on, ask whether to continue with marked assumptions. Do not begin the verdict
until the user chooses. Low-impact unknowns do not need another round: assume a
reasonable value and flag it with `[assumed: <basis>]`.

Every assumption must be visible so a reader can see exactly what to push back
on. A verdict resting on four silent assumptions is worth less than one that took
two more questions to produce.

For the `audit` entry point: read the target implementation instead of asking the
user, then confirm the inferred frame in one message.

## Step 4 — Decompose and label

Read `framework/labeling.md`, then `framework/model-tiers.md`. Produce a step table
for the automation task with exactly one label per step (DETERMINISTIC, JUDGMENT,
or HUMAN). Count the JUDGMENT rows; carry this count into pattern selection.

Give every JUDGMENT row a tier — WEAK, MID, or STRONG — by the tests in
model-tiers.md, and name which of the three questions set it. Start at the weakest
tier that could work and move up only when a named failure forces it; the reverse
default is the mistake this skill exists to catch, one level down. A JUDGMENT row
without a tier is an unfinished analysis, and the final gate rejects it.

## Step 5 — Select a pattern

Read `framework/patterns/README.md`, then open the specific pattern file the index
points to for the best match. If no pattern fits, use the escape hatch described in
the index and say so explicitly.

For pattern 04, compare the proposed deterministic verifier with every defined
harm in the action-and-blast-radius and tolerance slots. A schema, syntax, type,
compile, or test pass proves only what that check encodes. If any relevant harm
remains unverified, compose with pattern 06 and put every passing model-generated
candidate through HUMAN approval before the consequential action.

## Step 6 — Write a temporary verdict

Read `framework/verdict-template.md`. Write the canonical verdict as temporary
Markdown in a writable workspace. The file is an internal representation, not
the user deliverable. Derive `<slug>` from the use-case title and reserve the
final filename `YYYY-MM-DD-<slug>.html`.

The verdict must use the exact section headings from the template, in the template's
order. Inventing headings, or omitting sections, produces a document that is not a
verdict. For the `audit` entry point, include the migration section the template
describes; otherwise omit it. For a multi-unit audit, include the inventory and
unit-verdict sections as well, and keep the level-2 sections describing the system
as a whole.

## Step 7 — Verify the temporary verdict

From the skill's own directory, run:

    python check_verdict.py <path-to-verdict>

Fix every violation the checker reports. Re-run until it reports zero violations.
Do not render or present a report until the checker passes.

## Step 8 — Render and deliver HTML

After the checker reports zero violations, run from the skill's own directory:

    python render_verdict.py <temporary-verdict.md> <final-report.html>

In Claude chat and mobile, write the final report in the code-execution sandbox
and return `YYYY-MM-DD-<slug>.html` as a downloadable HTML attachment. In Cowork,
write it into the task's writable workspace. In Claude Code and Codex, and in any
other persistent workspace, write it to
`docs/verdicts/YYYY-MM-DD-<slug>.html`.

Remove the temporary Markdown only after successful rendering has atomically
created or replaced the HTML report. If checking or rendering fails, preserve the
temporary Markdown for diagnosis and do not present any partial HTML.

Deterministic validation requires Python 3 or equivalent Python code execution.
If it is unavailable, explain that requirement and stop. Do not skip or downgrade
validation to a model-only review.

## Rules that always apply

- The answer may be that a genuine agent loop is correct — say so explicitly when
  the conditions in pattern 07 are met.
- Address the agent-loop alternative in every verdict, even when rejecting it.
- Every JUDGMENT row carries a tier. The label says a model is needed; the tier
  says which one, and the strongest is not the default.
- For pattern 04, complete the verifier contract in the verdict template. Never
  infer semantic correctness from a proxy check.
- Never generate implementation code. The deliverable is the HTML verdict report.
- A verdict that has not passed `check_verdict.py` and `render_verdict.py` is not
  finished.
