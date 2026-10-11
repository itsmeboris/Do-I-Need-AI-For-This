# 01 — Don't build it

## When it applies

The cadence-times-time-saved arithmetic does not repay the cost of building and
maintaining the automation. This is not a technical verdict — it is an economic
one. A task that fires three times a year and saves ten minutes each time does
not justify two weeks of build work plus annual maintenance. The person doing the
task manually costs less.

The arithmetic form:

```
(runs per year × minutes saved per run) vs (build hours + annual maintenance hours)
```

Convert both sides to the same unit (hours, or cost at a blended rate). If the
right side exceeds the left side's present value over a reasonable horizon,
do not build the automation.

This pattern also applies when the problem is not worth solving at the current
moment regardless of the numbers — a one-off cleanup that will never recur, a
manual step that a pending migration will eliminate, or a task that is already
on someone's roadmap to restructure entirely.

## When it does not

- The arithmetic is marginal but the automation provides reliability, auditability,
  or correctness guarantees that have value beyond raw time saved — recalculate
  with those benefits priced in.
- The task recurs unpredictably and a manual response is slow enough to cause real
  harm when it fires unexpectedly — latency has cost too.
- The automation is a learning exercise or a platform investment, not just a
  per-task optimization.

## Shape

```
(no system is built)
```

The output of this pattern is a written recommendation: state what was evaluated,
show the arithmetic, and record why the build was not worthwhile. That record
prevents the same question from being re-litigated in six months without the
context that was available now.

## Cost profile

Zero build cost, zero operational cost, zero maintenance cost. The cost of not
building is the time spent on the manual task over the horizon, minus whatever
benefit the automation would have provided. If the arithmetic checked out, that
cost is lower than building.

## Failure modes

- **The time estimate is wrong in the author's favor.** Build hours are often
  underestimated and minutes-saved are often overestimated. Be conservative on
  both. The first estimate of how long a build takes is almost always too low
  by a factor of two or three once edge cases, testing, deployment, and
  documentation are included.
- **Maintenance cost is omitted.** A working automation requires upkeep: schema
  changes break parsers, APIs change, credentials rotate, and alerting drifts.
  Annual maintenance is rarely zero and frequently exceeds the original build cost
  over a three-year horizon.
- **The decision is not recorded.** Without a written record, the same evaluation
  is repeated by a new team member who does not know it was already done. Write
  the arithmetic down even when the answer is "do not build."

## Degrades into

Any other pattern if the arithmetic is re-evaluated and the conclusion changes —
for example, because the cadence increased, the minutes-saved estimate was
revised upward, or a platform investment made the build significantly cheaper
than originally projected.
