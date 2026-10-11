# Pattern Catalog

Patterns are composable. Real systems are frequently one pattern wrapping another:
a batch inference run (03) whose results each go through generate-then-verify (04),
or an event-triggered bounded agent (05) that terminates with a propose-and-approve
step (06). The entries here name the dominant shape; they do not forbid nesting.

## Index

| id | pattern | applies when |
| --- | --- | --- |
| [`00-no-ai`](00-no-ai.md) | No AI | every step is DETERMINISTIC |
| [`01-dont-build-it`](01-dont-build-it.md) | Don't build it | cadence times time-saved does not repay build plus maintenance |
| [`02-pipeline-one-agent-call`](02-pipeline-one-agent-call.md) | Deterministic pipeline, one agent call | exactly one JUDGMENT row, between deterministic acquire and act |
| [`03-batch-inference`](03-batch-inference.md) | Batch inference | high volume, per-item judgment, no tools, no loop |
| [`04-generate-then-verify`](04-generate-then-verify.md) | Generate then verify | output is machine-checkable; cheap model plus verifier beats expensive model plus trust |
| [`05-event-triggered-bounded-agent`](05-event-triggered-bounded-agent.md) | Event-triggered bounded agent | genuine tool use required, event trigger, hard turn cap enforced |
| [`06-propose-and-approve`](06-propose-and-approve.md) | Propose and approve | the action step carries a HUMAN label; a person must authorize |
| [`07-genuine-agent-loop`](07-genuine-agent-loop.md) | Genuine agent loop | steps unknown in advance, each step depends on the last, no deterministic driver possible |

## Selection guide

Start from the labeled decomposition produced by the frame and labeling stages.

1. **Route on the HUMAN label first, then count.** If the action step carries a
   HUMAN label, the answer is 06 regardless of the JUDGMENT count — the
   authorization requirement defines the pattern, not how many judgment steps
   precede it. If no HUMAN label appears on the action step: zero JUDGMENT rows
   points to 00 or 01; one JUDGMENT row points to 02, 03, or 04 — unless making
   that judgment requires tool calls to gather context that cannot be assembled
   deterministically before the model runs, in which case the candidate is 05;
   more than one JUDGMENT row points to 05 or 07.

2. **Check the trigger and blast radius.** An event trigger with bounded tool use
   points to 05. A HUMAN label on the action step points to 06. A step count that
   is genuinely unknowable in advance, where each step depends on the last, points
   to 07 — but 07 has conditions that must all hold before it is the right answer
   (see that file).

3. **Check volume and the verifier boundary.** A single-judgment decomposition
   at high volume with per-item decisions and no tools is 03. The same
   decomposition where the output is machine-checkable and bounded retry is
   acceptable is 04 only if the deterministic verifier covers every defined
   harm. Syntax, schema, type, compilation, and test checks prove only the
   properties they encode. If a passing output can still cause a relevant
   semantic or production harm, compose 04 with 06 and route every passing
   model-generated candidate through HUMAN approval before the action.

4. **Check whether you actually need to build anything.** Before selecting any
   pattern, confirm that the cadence-times-time-saved arithmetic favors building.
   If it does not, the answer is 01 regardless of the JUDGMENT count.

## Escape hatch

If no pattern in this catalog fits the decomposition, do not force the task into
the nearest slot. Compose the architecture directly from the labeled steps and
state explicitly that no catalog entry applied.

Forcing a task into the wrong slot is a worse outcome than admitting the catalog
is incomplete: it produces a verdict that names the wrong pattern, which misleads
anyone who uses it as a reference later. Incomplete catalogs are correctable;
wrong verdicts accumulate.

If the escape hatch is used repeatedly for tasks that share a common shape, that
is the signal that the catalog needs a new entry. Document the shape, the
conditions under which it applies, and the failure modes before adding the entry.
