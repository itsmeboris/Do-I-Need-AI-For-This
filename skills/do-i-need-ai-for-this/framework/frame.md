# The Frame

A use-case frame is a structured set of eight slots that captures everything
needed to decompose an automation idea before any architecture is proposed.
Fill the slots from what the user has already said; ask only what is genuinely
missing.

The frame exists because automation ideas arrive as intentions, not
specifications. An architect who proceeds without it will make one of two
mistakes: building an agent loop for work that is deterministic, or building a
deterministic pipeline for work that requires judgment. Neither is correctable
without rewriting the architecture. The frame surfaces that question before any
design decision is made.

## Slots

### Trigger

**Captures:** what causes this work to start.
**Resolved when:** the user has named one of: a human request, an external event, a clock, or a condition someone is currently watching for by hand.
**If unknown:** apply the question policy below; after authorized assumptions, use a schedule and flag that an event source was not investigated.

The trigger determines more of the final architecture than any other slot. A
condition that "someone keeps an eye on" is almost never a genuine polling
requirement — it is an event whose notification channel has not been found yet.
Push for the event before accepting the poll.

### Cadence and volume

**Captures:** how often the trigger fires and how many items arrive each time.
**Resolved when:** the user has named an approximate frequency and a rough upper bound on batch size, even if both are estimates.
**If unknown:** apply the question policy below; after authorized assumptions, use low frequency (daily or less) and small batches (under 100 items), and flag that neither was confirmed.

Volume decides whether a judgment-heavy approach is affordable. An agent that
carefully evaluates each item may be entirely appropriate at ten items per day
and wildly impractical at ten thousand per hour. Confirm the scale before
committing to any architecture that processes every item individually — the
design that is correct at one volume is often wrong at another.

### Inputs

**Captures:** what data or artifacts the automation receives when it starts.
**Resolved when:** the user has named every input and the system or format that produces it.
**If unknown:** apply the question policy below; after authorized assumptions, use whatever the trigger event naturally carries and flag that the input contract was not confirmed.

Inputs define the information boundary. An agent that must make a judgment call
with an incomplete input is a worse outcome than discovering the missing field
and fetching it deterministically beforehand. Before accepting this slot as
filled, check whether each input is available at trigger time or requires a
separate lookup — a lookup that may itself be deterministic.

### Decision

**Captures:** the choice or assessment the automation must make, and whether a deterministic rule can express it.
**Resolved when:** the user has either stated a rule that produces the right output for all inputs, or confirmed that no such rule can be written.
**If unknown:** apply the question policy below; probe for the rule before treating it as a potential judgment call.

This is the load-bearing slot. Most automation ideas that reach for AI are
deterministic rules that the author has not yet articulated. A rule that can be
stated in one sentence is not a judgment call, and the architecture should
reflect that. Reserve model invocations for the residual set of inputs where a
competent engineer familiar with the domain would genuinely pause before
deciding.

### Action and blast radius

**Captures:** what the automation does with its output, and how much damage an incorrect action causes.
**Resolved when:** the user has named the target system, the mutation that will occur, and whether that mutation is reversible.
**If unknown:** apply the question policy below; after authorized assumptions, treat the action as irreversible and production-affecting, and flag both assumptions.

Blast radius is the single most important constraint on whether an autonomous
architecture is acceptable. A writable action in an irreversible system requires
a proposal-and-approval stage or a hard limit on autonomy — not because approval
adds value, but because an undetected error has no recovery path. Do not let the
user skip past this slot.

### Success signal

**Captures:** how the system or a human knows the automation did the right thing.
**Resolved when:** the user has named a concrete, observable outcome that distinguishes a correct run from an incorrect one.
**If unknown:** apply the question policy below; after authorized assumptions, use human verification and flag the absence of an automated success signal.

Without a success signal there is no feedback loop and no way to discover
degradation over time. An automation that "just runs" is one that can silently
do the wrong thing indefinitely. Probe for anything the target system exposes —
a status field, a downstream metric, an exit code, a count change — before
accepting that human audit is the only option.

### Tolerance and review

**Captures:** the acceptable error rate and the mechanism for human intervention when the automation makes a mistake.
**Resolved when:** the user has named a threshold for errors before escalation and described how a human can inspect or override a decision.
**If unknown:** apply the question policy below; after authorized assumptions, use zero tolerance and mandatory human review, and flag that the threshold was not confirmed.

A stated tolerance is what distinguishes a production system from a prototype.
"It has to be correct" is a requirement statement, not a tolerance — it says
nothing about what happens when the system fails, which it eventually will. Every
automation needs a failure path routed somewhere before errors accumulate. The
tolerance also governs how much autonomy is safe: a high tolerance permits more
automation; a low one implies the blast radius was underestimated.

### Constraints

**Captures:** limits on latency, cost, privacy, compliance, or existing system boundaries that rule out otherwise-valid architectures.
**Resolved when:** the user has named any hard limits on time, money, data handling, or available systems.
**If unknown:** apply the question policy below; after authorized assumptions, use only constraints implied by the target environment and flag that constraints were not confirmed.

Constraints are easiest to miss and most expensive to discover late. A model
invocation that would otherwise be the clean architectural answer may be
forbidden by a data-residency rule. A real-time latency budget may rule out
batch processing entirely. Collect constraints before generating architecture
options — a verdict built on unstated constraints forces a rework of the entire
decomposition, not just one component.

## Rules

1. Never ask what the user already said. Parse the initial description into slots before asking anything.
2. Do not block indefinitely on a missing slot. First classify it using Step 3 in `SKILL.md`. Ask another round for decision-changing unknowns. If they remain unanswered, ask whether to continue with marked assumptions; low-impact unknowns may be assumed directly.
3. Ask at most three questions per message.
