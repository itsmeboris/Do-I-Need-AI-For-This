# 02 — Deterministic pipeline, one agent call

## When it applies

The decomposition has exactly one JUDGMENT row, and it sits between deterministic
acquisition and deterministic action. Everything before it can be fetched by an
API, a query, or a command. Everything after it is an API call, a commit, or a
write.

This is the most common correct answer for "watch X and react to it".

## When it does not

- Two or more JUDGMENT rows that depend on each other's results — consider 05.
- The action step is labeled HUMAN — that is 06.
- The judgment must be made per-item across a large batch — that is 03.

## Shape

```
trigger (event, else schedule)
  └─ deterministic: gather everything the decision needs
       └─ ONE model invocation: the decision, with all context supplied up front
            └─ deterministic: act on the structured result
                 └─ deterministic: confirm the action landed
```

The model is called once, with no tools. It receives a fully assembled context and
returns a structured result. It has no ability to wander, and no reason to.

## Cost profile

One invocation per event, not per unit of time. Cost scales with how often the
thing you care about actually happens, which is usually orders of magnitude below
how often you would have checked.

Latency is one model round-trip plus the deterministic work, and the deterministic
work is parallelisable.

## Failure modes

- **Context assembly misses something**, and the model answers confidently from a
  partial picture. Mitigate by making the gather step's output reviewable.
- **The structured result is not validated**, so a malformed response reaches the
  action step. Always parse into a schema before acting.
- **The single call quietly becomes a loop** when someone adds tools to it "just
  in case". If it needs tools, re-run the decomposition — the answer may now be 05.

## Degrades into

Pattern 07 when misapplied: give the single call tools and a retry, and you have
built an agent loop by accident, with none of the turn caps or cost ceilings that
07 requires.
