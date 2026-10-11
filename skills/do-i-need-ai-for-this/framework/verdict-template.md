# Verdict Template

A verdict is a structured recommendation: not a conclusion but an argument.
Each section earns its place by doing something the others cannot. Fill every
section; where evidence is thin, state the assumption explicitly.

The completed template is a temporary internal representation. Run
`python check_verdict.py <verdict.md>` from the skill's own directory to verify
section order, pattern identifiers, tier labels, and the other structural
requirements. Only after it passes, run
`python render_verdict.py <verdict.md> <report.html>` and deliver the HTML report.

## Restated use case

Restate the user's idea in terms of trigger, action, and observable outcome --
what the system will actually do, stripped of the intent that motivated it.
The purpose is not to paraphrase but to make the scope concrete. A reader who
has not seen the original description should be able to understand exactly what
runs, what it touches, and what it produces.

If any frame slot was assumed rather than stated, flag it here in brackets, for
example: [cadence assumed: daily]. This section is the contract the rest of the
verdict is arguing about; if it is wrong, every section that follows is wrong too.

## Inventory (multi-unit audits only)

This section appears only when the audit found more than one distinct (trigger,
blast radius) pair in the target. A single-unit audit and every verdict run omit
it entirely rather than leaving it empty. See inventory.md for the unit
definition, the grouping rules, and how the rank score is computed.

Open with one sentence naming where you looked — the registry, dispatch table,
command definitions, schedules — so a reader can judge the enumeration rather
than trusting it. Then the table, ordered by rank score, highest first. The `unit`
and `audited` columns are read by `check_verdict.py`; the rest are for the reader.
`audited` is `yes` or `no` and nothing else.

| rank | unit | trigger | blast radius | S | R | score | audited |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `example_worker` | dispatched per changed file | posts a comment on the merge request | 4 | 4 | 16 | yes |
| 2 | `example_renderer` | dispatched once per run | writes a PNG into the run's output folder | 3 | 2 | 6 | no |

### Not audited

One line per unit whose `audited` cell says `no`, naming the unit and the specific
reason. A rank score and a cut is a reason; "out of scope" is the omission
restated as though it explained itself.

- `example_renderer` — score 6, below the depth cut at the top 5 by rank.

This list and the unit verdicts together must account for every row in the table
above, exactly once each. That reconciliation is enforced; a verdict that inventories
twenty-seven units and discusses six fails the checker rather than shipping.

## Frame

Show the eight frame slots and their resolved values. Flag any slot that was
assumed rather than confirmed, using [assumed: <value>] inline so a reader can
see at a glance which parts of the analysis rest on inferred information.

In a multi-unit audit this section describes the system as a whole — the trigger
that starts a run, the blast radius of the run taken together, the tolerance the
operator holds the whole thing to. Per-unit slots go in the unit verdicts. The
orchestration is itself an architecture and gets its own verdict here.

Slot values that were confirmed by the user can be stated plainly. Slots that
were inferred from context or assumed in the absence of information must be
flagged. A verdict built on unacknowledged assumptions gives the reader no way
to identify where to push back.

Example layout:

- **Trigger:** a build-status change event from the CI API [assumed: webhook, not confirmed]
- **Cadence and volume:** ~200 builds per day, ~1 per push
- **Inputs:** build ID, stage name, exit code, last 200 lines of log
- **Decision:** is this failure novel, or does it match a known pattern?
- **Action and blast radius:** post a comment on the merge request [reversible: comment can be edited]
- **Success signal:** the engineer marks the comment resolved [assumed: no automated signal]
- **Tolerance and review:** one misclassification per week acceptable before escalation
- **Constraints:** response must arrive within 5 minutes of the build completing

## Decomposition

List the steps in execution order. Label each step DETERMINISTIC, JUDGMENT, or
HUMAN using the labeling rules from labeling.md. The label is not a rating of
difficulty -- it describes what kind of processing the step requires.

| # | step | label | tier |
| --- | --- | --- | --- |
| 1 | Fetch the build log from the CI API | DETERMINISTIC | — |
| 2 | Decide which subsystem the failure implicates | JUDGMENT | MID |
| 3 | Post the comment on the merge request | DETERMINISTIC | — |

Every JUDGMENT row names a tier from model-tiers.md -- WEAK, MID, or STRONG --
and says which of the three questions set it. DETERMINISTIC and HUMAN rows have
no tier; write `—`. `check_verdict.py` rejects a JUDGMENT row with no tier,
because a decomposition that says a model is needed without saying which one
leaves the most expensive assumption in the design unstated: the strongest model
available, chosen by default and never revisited. Start at the weakest tier that
could work and move up only when a named failure forces it.

A well-decomposed use case has a small number of JUDGMENT rows (often one) and
many DETERMINISTIC rows. Steps that feel like judgment are frequently deterministic
rules that have not been stated yet; probe for the rule before accepting the label.

Include both the main path and any error or escalation paths. A step that sends
a failure notification is as much a part of the decomposition as the step that
makes the decision.

## Recommended pattern

Name the pattern from the catalog that fits this decomposition and state why it
fits. Naming the pattern is not sufficient; the reader needs to understand which
properties of the decomposition drove the choice.

If the cadence-and-volume slot was critical to the decision, say so. If the
single JUDGMENT row is what made this a pipeline rather than a loop, say so. A
pattern recommendation without the reasoning is a label, not a verdict.

Reference the pattern file (e.g., 02-pipeline-one-agent-call.md) so the reader
can check the when-it-applies and when-it-does-not sections directly.

If the figure that drives the build-vs-don't-build decision is assumed rather
than measured, say so here — in the recommendation itself, not only in the
frame. A reader who skims to this section must not miss that the recommendation
rests on an assumed number. The form: name the figure and state that it is
assumed, for example: "*(Note: this recommendation rests on an assumed failure
rate; confirm before acting.)*" A recommendation whose deciding figure is assumed
but whose recommendation section reads as settled is incomplete.

When the recommendation includes `04-generate-then-verify`, include this exact
verifier contract in the recommendation:

- **Verifier proves:** [the deterministic property established by a pass]
- **Verifier does not prove:** [a named gap, or `none [basis: <formal
  specification, exhaustive rule, or equivalent deterministic evidence>]`]
- **Post-pass gate:** [`AUTOMATIC`, or `HUMAN — every generated candidate
  requires approval`]

The verifier boundary must be compared with every defined harm in the Frame. A
schema, syntax, type, compile, or test pass does not prove semantic correctness
unless the relevant semantics are encoded in that check. If the verifier leaves
any relevant harm unproved, the post-pass gate is HUMAN and the decomposition
must show that every passing model-generated candidate is reviewed before the
consequential action. Human review only after the verifier rejects a candidate
does not close this gap.

## Rejected alternatives

List every architecture considered and explain why each was rejected. The
agent-loop option (pattern 07-genuine-agent-loop) must appear in this section in
every verdict, whether or not the user proposed one. A recommendation without
its rejected alternatives is an assertion rather than an argument -- the reader
cannot evaluate whether the recommendation is correct unless they can see what
was ruled out and why.

For the agent-loop rejection, address the conditions checklist from
07-genuine-agent-loop.md explicitly: which condition does this use case fail?
That is usually the argument that closes the case.

## Failure modes

List the ways the recommended architecture can fail, and describe how each
failure manifests. A failure mode is not the same as a rejected alternative --
it is a way the chosen architecture behaves incorrectly despite being the right
design.

For each failure mode, state whether the failure is detectable (does the success
signal catch it?), and what the recovery path is (does the blast-radius slot
provide an out?). A failure mode with no detection and no recovery is a gap in
the design, not just a risk to acknowledge.

## Revisit when

State the specific conditions under which this verdict should be reconsidered.
These are not generic caveats -- they are concrete changes to the frame slots
that would shift the pattern recommendation. For example: if volume grows above
X events per hour, or if the blast radius changes from reversible to irreversible.

A verdict without a revisit condition is implicitly claimed to be durable under
all future conditions. That claim is almost always false.

## Next step

State the single concrete action the reader should take before doing anything
else. Not a list of next steps -- one step. The one that unblocks everything
else, or the one that would falsify a critical assumption if the answer came back
wrong.

If the most important assumption in the Frame section was not confirmed, the next
step is usually to confirm it. If the frame is solid and a pattern was
recommended, the next step is usually to build the deterministic gather stage and
verify the inputs are available.

## Unit verdicts (multi-unit audits only)

One level-3 subsection per unit whose `audited` cell says `yes`, in inventory
order. The heading names the unit exactly as the inventory row does, so the two
can be matched; anything after the name is free text.

Each subsection is a condensed verdict for that unit alone, carrying three things:

- **Frame:** only the slots that differ across units — trigger, cadence and
  volume, action and blast radius, tolerance and review. Slots that are identical
  for every unit belong in the system-level Frame section, not repeated here.
- **Decomposition:** the labelled steps for this unit, with the JUDGMENT count
  and the tier on every JUDGMENT row.
- **Pattern:** a canonical pattern ID from the catalog, or `escape-hatch`, with
  the property of this unit's decomposition that drove the choice. The checker
  requires the ID here for the same reason it requires one at system level: a
  pattern name without an ID is a label nobody can look up.
The point of the per-unit pass is the comparison it enables: which units use
model judgment for work that a rule could do, and which use a stronger tier than
their judgment needs. Neither question has an answer at system level, which is
why the level-2 sections cannot carry them.

### Example unit — one subsection per audited unit

- **Frame:** trigger, cadence, action and blast radius, tolerance for this unit.
- **Decomposition:** the step table, one label per step, a tier on the JUDGMENT
  rows.
- **Pattern:** `02-pipeline-one-agent-call` — one JUDGMENT row between a
  deterministic gather and a deterministic write.

## Migration (audit entry point only)

This section appears only in audit-mode output, when the verdict is analyzing an
existing agent loop rather than a new automation idea. A verdict run omits this
section entirely rather than leaving it empty.

In audit mode, this section holds a table of steps currently inside the agent
that should be lifted out and implemented as deterministic pipeline stages. The
table is ordered by waste removed divided by effort to extract, with the expected
reduction in invocations per day stated for each step. The section closes with a
single "change this first" line naming the highest-priority extraction.

| step currently inside the agent | label if extracted | invocations reduced per day | extraction effort |
| --- | --- | --- | --- |
| Example: fetch build log from CI API | DETERMINISTIC | ~200 | low (one API call, structured response) |
| Example: check exit code against known-bad list | DETERMINISTIC | ~180 | low (lookup against a maintained table) |

**Change this first:** [name the single highest-priority step here].
