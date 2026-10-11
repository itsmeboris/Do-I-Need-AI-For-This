# Labeling

Every step in the decomposition gets exactly one label: DETERMINISTIC, JUDGMENT,
or HUMAN. Assign the label before proposing an architecture. The label is the
verdict; the architecture follows from it.

The three labels are not a spectrum. A step does not become JUDGMENT because it
is complex, or HUMAN because it is important. Each has a precise test. Use the
test.

## DETERMINISTIC

**Test:** Can you write the rule down?

If the mapping from inputs to output can be stated as a rule — even a long or
conditional one — the step is DETERMINISTIC. A rule does not have to be simple.
Regex, lookup tables, multi-stage pipelines, and statistical thresholds are all
rules. The question is whether the rule exists and can be encoded, not whether
it already has been.

The following operations feel intelligent and are not:

- **Parsing** structured or semi-structured input (logs, stack traces, diffs,
  manifests, API responses) — the format is a contract; write the parser.
- **Filtering** a result set by stated criteria — the criteria are the rule.
- **Thresholding** a numeric signal — the threshold is a number someone chose;
  code it.
- **Lookups** against a known mapping (error code to severity, filename to owner,
  status to next action) — the mapping is data; load it.
- **Diffing** two artifacts to find what changed — the diff algorithm is
  deterministic; apply it.
- **Sorting** a list by a defined key or score — the comparator is a rule; write
  it.
- **Formatting** output into a required shape or template — the template is a
  specification; render it.
- **Retry logic** — the backoff policy is a rule; express it as one.
- **Deduplication** of records by key or content hash — the identity criterion is
  a rule; implement it.

Before labeling any of these JUDGMENT, ask whether you have simply not written
the rule down yet.

**Commonly mislabelled as judgment:** steps that feel ambiguous because the rule
has not been articulated. The rule almost always exists. Find it.

## JUDGMENT

**Test:** Would two competent engineers have to discuss it?

A step is JUDGMENT when it meets either of the following conditions:

1. The input is open-ended natural language, creative content, or a description
   of a situation that cannot be reduced to a canonical form; or
2. The decision space cannot be enumerated — there is no finite list of
   categories or outcomes that covers all cases, and a rule covering all cases
   cannot be written down.

If neither condition is met, the step is DETERMINISTIC. The threshold between
"two engineers would agree instantly" and "two engineers would have to discuss
it" is the operative signal. If the right output for a given input is obvious to
any competent practitioner, a rule can produce it.

The count of JUDGMENT rows in a decomposition is the single most informative
output of this process. In a well-analyzed system it is usually one. Build the
judgment call well; build everything around it deterministically.

Every JUDGMENT row also carries a tier — WEAK, MID, or STRONG — naming how
capable a model the step actually needs. The label and the tier answer different
questions: the label says a model is required, the tier says which one. See
model-tiers.md for the three tiers and the test that picks between them. A
JUDGMENT row without a tier is an unfinished analysis, and `check_verdict.py`
rejects it.

**Commonly mislabelled as judgment:** steps where the author has not yet
articulated the rule. If you can describe what output would be wrong, you are
usually close to describing what rule produces the right one.

## HUMAN

**Test:** Is the constraint authority rather than capability?

A step is HUMAN when the requirement is not that a capable system execute it,
but that an accountable person do so. The question is not whether a model would
get it right — it often would. The question is who bears responsibility when it
does not.

Do not soften this label into "risky things." Risk and reversibility are covered
by the action-and-blast-radius frame slot. HUMAN is specifically about authority
and accountability. A step is HUMAN when the organization requires a named
person, a role, or a committee to have made the decision — regardless of what
any automated system could produce.

Examples: merging to a protected branch, spending money above a threshold,
contacting a customer to communicate a commitment, signing off on a compliance
artifact. A model may produce excellent input for all of these. The step is
still HUMAN.

**Commonly mislabelled as judgment:** steps where a model would produce a
recommendation and a human would accept it nearly every time. The acceptance
rate is irrelevant. If someone must be accountable for the outcome, the step is
HUMAN.

## Boundary cases

- "Parse the log for the failing stage" feels like judgment and is not. The log
  has structure; write the parser.
- "Read the stack trace and decide which of three subsystems is at fault" is
  judgment. The mapping is not written down anywhere.
- "Decide whether this fix is safe to merge" is HUMAN, not JUDGMENT, even if a
  model would usually guess correctly. Capability is not the question.
- Routing a support ticket to the correct queue by matching subject and body
  against documented criteria is DETERMINISTIC. The routing rules exist in a
  runbook; they have just not been encoded yet.
- Approving a payment above an authorization threshold is HUMAN. This is not
  because models cannot assess payment risk — it is because someone must be
  accountable when the assessment is wrong.
- Classifying a free-form support ticket into one of twelve fixed category tags
  is JUDGMENT. The output space is enumerable — twelve options — but the input
  (the ticket text) is open-ended natural language for which no rule covers all
  cases. Condition 1 alone is sufficient. Contrast with the routing-against-documented-criteria
  example above: that case is DETERMINISTIC because explicit criteria exist that
  can be stated as a rule. When no such criteria exist, classifying free text
  into a small fixed set is still JUDGMENT.
- Tagging that ticket and choosing which subsystem a stack trace implicates are
  both JUDGMENT and do not want the same model. One has a right answer over a
  short input; the other reconciles several sources and nothing downstream
  disagrees with it. The label does not separate them and is not meant to — that
  is what the tier is for. See model-tiers.md.

## The headline number

The count of JUDGMENT rows is the single most informative output of the
decomposition. It is usually one. Almost everything else — parsing, routing,
filtering, formatting, retrying, diffing — is DETERMINISTIC once the rule is
stated. Almost everything that requires authority — merging, spending, committing
to a customer — is HUMAN.

People routinely build systems in which the judgment label is implicitly applied
to all steps, because no one sat down to ask which steps actually require it.
The result is a system that is unnecessarily opaque, unnecessarily expensive, and
impossible to audit. The explicit count makes that default visible and
reversible.

The same default operates one level down, on the rows that survive. An analysis
that removes four unnecessary model calls and then silently assumes the most
capable model for the one that remains has done half the job. Tier every
JUDGMENT row, and start at the weakest tier that could work rather than the
strongest — the argument in model-tiers.md is this one, applied to model choice
instead of to model use.
