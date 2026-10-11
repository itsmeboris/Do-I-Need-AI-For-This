# 04 — Generate then verify

## When it applies

The decomposition has one JUDGMENT row whose output is machine-checkable. The
model generates a candidate result, and a deterministic verifier assesses whether
that result is correct with respect to every defined harm in the Frame. If the
candidate fails verification, the system retries with a bounded number of
attempts before escalating or discarding the result.

The trade is explicit: a cheap model plus a deterministic verifier plus bounded
retry beats an expensive model plus trust. The verifier is the architectural
investment — it must be written and maintained — but it replaces per-item human
review and catches errors that even expensive models make.

“Machine-checkable” means more than syntactically valid. The verifier is complete
only when its acceptance rule rejects every candidate that could cause the
defined harm. A schema validator proves shape and type constraints; it does not
prove that a generated field substitution preserves meaning unless that semantic
mapping is itself encoded in the schema or another deterministic check.

## When it does not

- The output is not machine-checkable — there is no deterministic criterion that
  distinguishes a correct result from an incorrect one. In that case the verifier
  cannot exist; use 06 to route the output to human review instead.
- The verifier checks only a proxy for correctness, such as syntax, schema shape,
  type safety, compilation, or test coverage, while the defined harm depends on
  semantics that the proxy does not detect. Pattern 04 may still generate and
  reject obviously bad candidates, but it must compose with 06: every passing
  model-generated candidate goes through HUMAN approval before the consequential
  action.
- Verification requires another model call — that is not a verifier, it is a
  second judgment step, and the decomposition should be re-run.
- The retry budget is unbounded or the failure mode is undefined — this pattern
  requires a hard cap on attempts; without one it is 07 in disguise.

## Shape

```
trigger (event or batch item)
  └─ deterministic: gather context
       └─ model invocation: generate candidate result
            └─ deterministic verifier: check the candidate
                 ├─ pass and verifier covers every defined harm: act on the result
                 ├─ pass with any unverified harm: HUMAN approval, then act
                 └─ fail: retry up to N times
                      └─ N failures: escalate or discard
```

The verifier is deterministic. It may call external systems (a compiler, a test
runner, a schema validator, an API endpoint) but it does not invoke a model.
Each retry receives the previous failure's diagnostics so the model can correct
its approach.

Before selecting this pattern, write a verifier contract:

- **Verifier proves:** the exact deterministic property established by a pass.
- **Verifier does not prove:** any relevant property or harm left outside that
  boundary. Write `none` only when a formal specification, exhaustive rule, or
  equivalent deterministic basis covers every defined harm.
- **Post-pass gate:** `AUTOMATIC` only when the unverified set is empty and the
  basis is named; otherwise `HUMAN`, with every generated candidate reviewed
  before the action.

A low retry rate, a high confidence score, or a passing proxy check does not
expand the verifier's proof boundary.

## Cost profile

Cost is bounded by `(retries + 1) × per-call cost`. The maximum is known at
design time. In practice, most items pass on the first or second attempt, so the
average cost is well below the maximum.

The verifier has a fixed cost per check. Choose that cost carefully if verification
is itself expensive (for example, a full test suite run per candidate). A
verifier that costs more than the model call negates the economic argument for
the pattern.

The larger saving is usually not the retry arithmetic but the tier. A model tier
is set partly by what a wrong answer costs (model-tiers.md); a deterministic
verifier drops that cost to the price of a retry, so the model no longer has to
be right every time — only often enough that the retry budget holds. Same
invocations, same tokens, an order of magnitude less per token. This is the one
place in a design where the weakest tier is defensible without argument, because
the verifier rather than the model is what makes the output trustworthy.

The reduction is only as wide as the proof boundary. Whatever the contract's
**Verifier does not prove** line names is still carried by the model alone, and
that residue sets the tier: a schema check against a semantic harm buys no tier
reduction on the semantic part of the judgment, only a HUMAN post-pass gate. So
that line does two jobs — it decides the gate, and it decides how far the tier
can fall. Read the tier off the unverified residue, not off the whole step.

## Failure modes

- **The verifier is too weak.** A verifier that passes incorrect results provides
  false confidence. Define what "correct" means precisely — ideally from a formal
  specification — before writing the verifier. Compare that definition with the
  Frame's action, blast radius, success signal, and tolerance; any relevant harm
  outside the verifier boundary requires a HUMAN post-pass gate.
- **The retry limit is set by intuition rather than measurement.** Set the cap
  by measuring first-pass and second-pass success rates on a representative sample.
  A cap of three is often sufficient; a cap of ten is a sign the model is wrong
  for this task.
- **Escalation is not handled.** When the retry budget is exhausted, the result
  must go somewhere — to a queue for human review, to a dead-letter store, or to
  an explicit failure report. Dropping it silently is the most common mistake.

## Degrades into

Pattern 06 when escalation is reached frequently enough that the human review
queue becomes the dominant workflow. If that happens, the verifier is too weak
or the model is wrong for the task — fix one of those before adding more retries.
