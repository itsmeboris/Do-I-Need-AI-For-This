# 00 — No AI

## When it applies

The decomposition has zero JUDGMENT rows. Every step maps to a rule that can be
stated, a threshold someone chose, a lookup against known data, or a format
defined by a specification. The automation may be complex — multi-stage,
branching, high-volume — but complexity does not imply judgment.

This pattern also applies when the only step that felt like judgment was a
heuristic someone had quietly encoded already: a threshold, a keyword filter, a
length cutoff. If the rule exists, write it down and label the step DETERMINISTIC.
The model invocation you were about to add is unnecessary.

## When it does not

- At least one step requires weighing open-ended inputs against a standard that
  cannot be reduced to a rule — label that step JUDGMENT and use a different
  pattern.
- A HUMAN label appears anywhere — even a purely deterministic pipeline with a
  required approval gate belongs in 06.
- The automation does not need to exist at all — check 01 first.

## Shape

```
trigger (event or schedule)
  └─ deterministic: fetch and normalize inputs
       └─ deterministic: apply rules, thresholds, or lookups
            └─ deterministic: act on the structured result
                 └─ deterministic: confirm the action landed
```

No model invocation appears in this shape. If one appears in implementation, the
decomposition was wrong, or the implementation drifted from the design.

## Cost profile

Zero inference cost. The only costs are compute, storage, and API calls to the
source and target systems. Latency is bounded by the deterministic steps and is
predictable at design time.

This is also the pattern with the lowest operational risk: every step is
inspectable, every output is reproducible given the same inputs, and the entire
pipeline can be tested against real data in a harness without touching production.

## Failure modes

- **A judgment step was encoded as a fragile heuristic.** The most common failure
  of this pattern is not that it stops working — it is that it keeps running while
  silently producing wrong outputs. A keyword filter approximating a judgment call
  has edge cases the author did not enumerate. The signal is a heuristic that
  requires periodic manual tuning, where no one can articulate what it optimizes
  for. Find that step, label it correctly, and route it through a model if it is
  genuinely irreducible.
- **Rules bitrot without a feedback loop.** A lookup table correct at deployment
  drifts as the source data evolves. Validate rule outputs against a sampled
  ground truth at regular intervals so degradation is detected before it
  accumulates.
- **The trigger is a poll that should be an event.** A purely deterministic
  pipeline attached to a tight poll loop is not a no-AI architecture win — it is
  a trigger design problem. Revisit the trigger slot before declaring the system
  complete.

## Degrades into

Pattern 02 if a genuine judgment call emerges that the rule set cannot cover and
a model invocation is added to handle it. That is the right response — but it
must be a deliberate architectural change with the decomposition re-run, not an
undocumented exception added to an otherwise deterministic pipeline.
