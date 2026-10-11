# 07 — Genuine agent loop

## When it applies

The number of steps required to complete the task is genuinely unknown before
execution begins, each step depends materially on the result of the previous one,
and no deterministic driver can enumerate the steps in advance. A person doing
this task by hand would not know how many actions they would need to take until
they had taken some.

This is a rare architectural shape. Most tasks that feel like they require an
agent loop do not: the step count is bounded and enumerable, the context can be
assembled upfront, or a deterministic driver can decide what to do next without
a model. Before accepting that this pattern is correct, exhaust every alternative.

## When it does not

- The step count is bounded and known at design time — use 05 with a hard cap.
- Context can be assembled fully before the model is invoked — use 02.
- The loop is needed because the model is not good enough on a single call, not
  because the task structure requires it — fix the single call.
- The action is irreversible and the blast radius is production-affecting without
  a human gate — the loop must terminate in 06, not execute autonomously.

## Shape

```
trigger
  └─ deterministic: establish initial context
       └─ agent: assess state
            └─ agent: decide and execute action
                 └─ deterministic: observe result
                      └─ agent: decide: continue loop or terminate
                           ├─ continue (turn N+1, up to hard cap): loop back
                           └─ terminate: produce structured result
                                └─ deterministic: validate and act
```

Two constraints are non-negotiable: a hard turn cap enforced by the caller, and
a cost ceiling that triggers early termination if exceeded. Neither is optional.
An agent loop without both is not this pattern — it is an unbounded process with
no architectural guarantees.

## Cost profile

Cost is unbounded within the cap-times-ceiling envelope. The only guarantee is
the maximum: `cap × (max tokens per turn × per-token cost)`. In practice the
average is much lower, but the budget must be planned against the maximum.

The turn cap is not a performance target — it is a safety limit. If the task
regularly reaches the cap, either the task is wrong for this pattern, the cap is
too low, or the model is getting stuck. Distinguish these three cases before
raising the cap.

## Failure modes

- **The loop runs without making progress.** A model that calls the same tool
  repeatedly with the same arguments, or that produces observations that do not
  change its next action, is not converging. Detect this with a check for
  repeated actions and terminate early.
- **The turn cap is raised under pressure.** The cap exists because someone
  calculated a safety bound. Raising it because a task hit the cap is a policy
  change, not a bug fix. Treat it as one: document why the original bound was
  wrong and what the new bound is based on.
- **Cost accumulates silently.** A loop that completes in one turn most of the
  time but occasionally runs to the cap produces a cost distribution with a
  heavy tail. Monitor the tail, not the average.
- **The output is not validated.** A loop that terminates after many turns and
  returns free-form text without schema validation has produced an unactionable
  result. Validate the output schema before the action step, and treat
  non-conforming output as a failure, not a warning.

## Degrades into

An unbounded process if either safety constraint — the turn cap or the cost
ceiling — is removed or systematically bypassed. That is not a degraded version
of this pattern; it is an architecture with no guarantees, which this tool was
built to prevent.

## Conditions that must all hold

The following conditions must all hold before this pattern is the correct answer.
If any is absent, a simpler pattern applies.

- [ ] The number of steps required to complete the task is genuinely unknown
  before execution begins — not just difficult to enumerate, but structurally
  unknowable without executing some steps first.
- [ ] Each step depends materially on the result of the previous one — the next
  action cannot be determined without observing what the last action produced.
- [ ] No deterministic driver can decide what to do next — the decision requires
  the model's judgment, not a rule or a lookup.
- [ ] A hard turn cap and a cost ceiling are defined, enforced by the caller, and
  sized against a worst-case analysis of the task's decision tree — not set by
  feel.
- [ ] The failure mode when the cap is hit is specified: the result is routed to
  a human handler or discarded, never retried with a higher cap without a policy
  decision.
