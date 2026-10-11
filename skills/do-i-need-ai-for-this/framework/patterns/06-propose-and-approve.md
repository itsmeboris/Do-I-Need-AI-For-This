# 06 — Propose and approve

## When it applies

The action step in the decomposition carries a HUMAN label. The system can
assemble context, generate a proposal, and route it to a person — but the actual
execution of the action requires a named, accountable human to authorize it. The
requirement is not that a capable system would get it right; it is that a person
must be responsible when it does not.

This pattern is the correct response whenever the blast radius, compliance
requirements, or organizational accountability policy forbids autonomous action.

## When it does not

- The action is fully reversible, the blast radius is low, and no policy requires
  human authorization — the HUMAN label was a misapplication; re-examine using
  pattern 02 or 05.
- The thing labeled HUMAN is actually a judgment step that requires expertise but
  not authority — route it through the model with higher care (02 or 05), not
  through a human queue.
- The approval is a formality that never results in rejection — see "rubber
  stamping" in Failure modes below.

## Shape

```
trigger (event or schedule)
  └─ deterministic or agent: assemble context; generate proposal
       └─ deterministic: format proposal for human review
            └─ HUMAN: review and authorize (or reject)
                 ├─ authorized: deterministic: execute action
                 └─ rejected: deterministic: log rejection; optionally notify
```

The proposal must carry everything the reviewer needs to make an informed
decision without additional research. A reviewer who must look up context before
approving is not reviewing — they are doing the work the system should have done.

## Cost profile

One model invocation (or one bounded agent run) plus a human review step per
event. The human cost is the dominant cost. It scales with the number of
proposals generated, not with the size of the items — volume decisions happen
at the trigger slot, not here.

If the human review step is a bottleneck, the answer is not to bypass it but
to reduce proposal volume (by improving filtering upstream) or to make the
review interface faster.

## Failure modes

- **Rubber-stamping.** The review must be cheap enough to actually happen. A
  proposal that takes fifteen minutes to evaluate, arrives at an unpredictable
  time, and is never rejected will eventually be approved without reading. When
  that happens the HUMAN label is a fiction — there is no real accountability,
  only the appearance of it. If the review cannot be done in under two minutes
  with the information provided, either improve the proposal or accept that the
  step is not genuinely human-gated.
- **The proposal omits context the reviewer needs.** A reviewer who frequently
  asks follow-up questions before approving is signaling that the proposal
  assembly step is incomplete. Fix the assembly step, not the review process.
- **No rejection path.** A system that has no mechanism for a reviewer to reject
  or request changes has built a rubber-stamp workflow regardless of intent.
  Model the rejection path before deployment.

## Degrades into

Pattern 05 if the human approval step is removed and the action is made
autonomous. That is sometimes the right evolution — once the system has
demonstrated high accuracy over a large sample, the accountability argument
weakens — but it must be a deliberate policy decision, not an operational
convenience.
