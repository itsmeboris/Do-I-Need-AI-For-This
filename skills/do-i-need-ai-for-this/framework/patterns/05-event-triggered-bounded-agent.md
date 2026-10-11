# 05 — Event-triggered bounded agent

## When it applies

The decomposition has one or more JUDGMENT rows that require tool calls to gather
context that is not available at trigger time. The agent must query systems,
inspect results, and decide its next action based on what it finds — but the
trigger is a discrete event, not a continuous polling loop, and the total number
of tool calls is bounded in advance.

This pattern is correct when the information needed to make the judgment cannot
be assembled deterministically before the model is invoked, because the right
next query depends on the answer to the previous one.

## When it does not

- All context can be assembled deterministically before the model is invoked —
  use 02 instead. A model that uses tools only to gather information that a
  deterministic step could have gathered is an unnecessary agent.
- The trigger is not a discrete event but a continuous condition — revisit the
  trigger slot; the architecture should not poll.
- The number of steps is genuinely unknowable in advance and depends on
  conditions the model discovers at runtime — that is 07, which has harder
  conditions that must all hold.

## Shape

```
event trigger
  └─ deterministic: extract trigger payload
       └─ agent turn 1: assess what information is needed; call tool(s)
            └─ agent turn 2: interpret results; call additional tools if necessary
                 └─ (up to cap)
                      └─ agent final turn: produce structured result
                           └─ deterministic: validate result schema
                                └─ deterministic: act on the result
```

The turn cap is enforced by the caller, not by the model. If the cap is reached
before a structured result is produced, the run is terminated and the event is
routed to a failure handler — not retried with a higher cap.

## Cost profile

Cost is bounded by `turns × average-tokens-per-turn × per-token-cost`. The
maximum is known at design time. Choose the cap based on the actual decision
tree: count the number of distinct tool call sequences the task requires in the
worst case, add a margin of one or two turns for error correction, and set
the cap there. A cap set by feel rather than analysis tends to be either too low
(causing spurious failures) or too high (allowing runaway cost when the model
gets confused).

When the cap is hit, the correct response is to route the event to a human
handler, not to raise the cap. If the cap is hit frequently, the decomposition
is wrong: either the task requires more judgment than was modeled, or the tools
are not providing useful enough responses.

## Failure modes

- **The turn cap is set too high.** A cap of twenty turns on a task that should
  complete in three is a sign the model can loop without making progress. Monitor
  the distribution of actual turn counts in production; the cap should be close
  to the 99th percentile, not ten times it.
- **Tool errors are not handled.** A tool call that returns an error must be
  handled explicitly — either by the model (if it can recover) or by the caller
  (if it cannot). An unhandled tool error consumes a turn and produces no useful
  information.
- **The structured output contract is not enforced.** An agent that terminates
  with free-form text instead of a validated schema cannot be acted on
  deterministically. Validate the schema before the action step; reject and
  escalate if it does not conform.

## Degrades into

Pattern 07 if the turn cap is removed or the number of steps is allowed to grow
without bound. Every genuine agent loop starts as a bounded agent with the cap
removed "just this once." Keep the cap.
