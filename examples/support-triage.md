# Support Triage Verdict

## Restated use case

When a support request arrives, classify its intent and draft a routing suggestion for an operator. The operator decides whether to apply the route. This is an illustrative example with fictional requirements, not a measured deployment.

## Frame

- **Trigger:** a new support request.
- **Cadence and volume:** about 40 requests per day [assumed: illustrative workload].
- **Inputs:** request subject and body.
- **Decision:** which support queue best matches the request's meaning?
- **Action and blast radius:** propose a queue; no ticket is moved automatically.
- **Success signal:** the operator accepts or corrects the proposal.
- **Tolerance and review:** every proposal is reviewed.
- **Constraints:** use only the submitted ticket text; preserve multilingual content.

## Decomposition

| # | step | label | tier |
| --- | --- | --- | --- |
| 1 | Normalize the submitted fields | DETERMINISTIC | - |
| 2 | Interpret the request intent | JUDGMENT | MID - multiple plausible intents must be reconciled |
| 3 | Approve or correct the proposed queue | HUMAN | - |
| 4 | Apply the approved queue | DETERMINISTIC | - |

## Recommended pattern

Use `06-propose-and-approve` composed with `02-pipeline-one-agent-call`: one bounded JUDGMENT step proposes a queue, and a HUMAN must authorize every move. The volume is assumed; confirm that the time saved justifies building this workflow.

## Rejected alternatives

`00-no-ai` cannot interpret novel free-form intent reliably. The agent loop in `07-genuine-agent-loop` is rejected because the steps are known in advance, there is no environment-driven iteration, and a deterministic stopping rule already exists.

## Failure modes

The classifier may misunderstand ambiguous language. Detection: the operator sees the original request beside the proposal. Recovery: the operator selects the correct queue before any move occurs.

## Revisit when

Revisit if requests become fully structured or if routing is ever allowed without operator approval.

## Next step

Collect a representative, non-sensitive set of previously corrected routing decisions.
