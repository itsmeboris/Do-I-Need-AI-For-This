# 03 — Batch inference

## When it applies

The decomposition has one JUDGMENT row that must be applied per-item across a
large batch. Volume is too high to review each item individually, no tool use
is required to make the judgment, and the items are independent of each other —
the decision for item N does not depend on the decision for item N-1.

The canonical shape is: a nightly or triggered job fetches a set of items,
classifies or scores each one with a single model call per item, and writes the
results to a store for downstream use.

## When it does not

- The batch is small enough that a single call with all items in context is
  cheaper and equally accurate — that is 02.
- Each item requires tool calls to gather context before the judgment can be made
  — that is 05 per item, which may be too expensive; re-examine the decomposition.
- The output of one item's judgment affects the next — items are not independent;
  the problem requires a different architecture.

## Shape

```
trigger (schedule or upstream completion)
  └─ deterministic: fetch the batch
       └─ deterministic: partition into chunks if necessary
            └─ per-item (parallelisable):
                 └─ ONE model invocation: classify or score the item
            └─ deterministic: collect and validate results
       └─ deterministic: write results to the target store
            └─ deterministic: report summary (counts, error rate)
```

No item produces a model call that inspects or affects another item's result.
The model has no tools and no memory across items.

## Cost profile

Cost scales linearly with batch size times the per-call cost. At high volume,
the difference between a cheap model and an expensive one compounds quickly —
select the smallest model that meets the accuracy requirement, then measure.

Parallelism controls latency. Most batch jobs are not latency-sensitive; the
constraint is usually throughput and cost, not wall-clock time.

## Failure modes

- **Accuracy is assumed rather than measured.** A batch job that classifies ten
  thousand items per night and is never sampled for accuracy will silently degrade
  as the distribution of input shifts. Sample a statistically significant subset
  of outputs against a ground truth at regular intervals. A sample of 200 items
  gives a 95% confidence interval of roughly ±7 percentage points for a 50%
  accuracy rate — measure from the start, not after a complaint.
- **Errors are swallowed silently.** A per-item call that times out or returns a
  malformed response should be logged and retried, not silently skipped. An error
  rate above a threshold should stop the batch and alert.
- **Throughput limits are ignored.** Firing all calls simultaneously against a
  rate-limited inference endpoint produces failures. Implement a concurrency cap
  and back-pressure before scaling up.

## Degrades into

Pattern 05 if per-item judgment requires tool calls to gather context that was
not available at batch assembly time. That is a more expensive architecture;
confirm that the judgment cannot be made from the information already in the batch
before accepting the upgrade.
