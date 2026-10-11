# Model Tiers

A JUDGMENT label says the step needs a model. It does not say which one. Those
are two questions, and answering only the first is how a design ends up calling
the most capable model available for work a much smaller one gets right every
time. Extracting fields from a document and choosing a system architecture are
both JUDGMENT; they want completely different models.

Every JUDGMENT row therefore carries a tier: WEAK, MID, or STRONG. The names are
positions in whatever lineup you can actually call, not particular models, and
that is deliberate — lineups turn over faster than architectures do, and a
framework that names products goes stale on the vendor's schedule rather than
its own. Whatever the current names are, the weakest one that does the step
correctly is the one to use. If a verdict names a concrete model, it names it in
passing as an example of a tier on the day the verdict was written; the tier is
the claim, the model is an illustration.

A tier is a property of the step, not of the author's confidence. Three things
about the step decide it: how much context has to be held at once, whether the
step has one right answer or several defensible ones, and whether a wrong answer
is caught downstream or escapes. The tests below ask those three questions in
the order that resolves the tier fastest.

## WEAK

**Test:** One right answer, over an input you could read in one sitting, with
something downstream that catches a wrong one?

If all three hold, the step is WEAK. Extracting named fields from a document,
tagging free-form text with one of a fixed set of categories, deciding whether
two records describe the same thing: each is JUDGMENT, because the input is
open-ended natural language and no rule covers every case. None is demanding. A
competent reader shown the same item twice answers the same way twice, the whole
input sits in front of them at once, and the next stage — a schema check, a
lookup that fails on an invented tag, a person glancing at a queue — notices
when the model is wrong.

**Commonly over-tiered:** high-volume classification. Volume is an argument for
the weakest tier rather than the strongest. The per-item price is multiplied by
the volume, and errors at that scale are visible in aggregate precisely because
there are so many items.

## MID

**Test:** Does the step reconcile several sources, choose among defensible
answers, or produce something nothing downstream will check?

Any one of the three puts the step at MID. Writing the summary of an incident
from a log, a diff, and a ticket that disagree with each other. Deciding which
of several subsystems a stack trace implicates. Drafting a message a person will
send. The work is bounded, but it holds more than one thing at a time, and the
output is judged rather than validated — two competent engineers could write
different answers and both defend them.

**Commonly over-tiered:** steps that are long rather than hard. A large input is
not a demanding judgment. A hundred-page contract read for one clause is a WEAK
step with a retrieval problem in front of it, and the fix is the retrieval, not
the tier.

## STRONG

**Test:** Is this the judgment the design exists to make — many defensible
answers, all the context held at once, and nothing downstream that checks it?

Reserve STRONG for the step where all three questions answer the wrong way at
once: choosing an architecture, diagnosing a novel failure with no matching
precedent, deciding what an ambiguous requirement should mean. These steps
exist, and when one is the reason the system is being built, pay for it.

Most decompositions have no STRONG row. One STRONG row is a plausible outcome. A
decomposition where every JUDGMENT row is STRONG is the mistake this framework
exists to catch, committed one level down.

## Choosing between them

| ask about the step | argues for a weaker tier | argues for a stronger tier |
| --- | --- | --- |
| how much context must be held at once | one artifact, or several that do not interact | several sources that must be reconciled against each other |
| how many answers are right | one, and a second reader would produce it | several, all defensible, and the choice must be justified |
| what a wrong answer costs | a later step catches it and retries | it reaches the action unchallenged |

The tier is the highest any single question forces. Two answers pointing at WEAK
do not average out the third: an unverified error that reaches production is not
made cheaper by the input being short.

Say in the verdict which question set the tier. "MID because the trace, the
recent changes, and the topology have to be reconciled" is a claim a reader can
disagree with. "MID" alone is a preference.

## Verification changes the tier

Read `patterns/04-generate-then-verify.md` before fixing any tier. A
deterministic verifier changes the answer to the third question, and the third
question is usually the one holding the tier up. With a verifier in place a
wrong answer costs a retry rather than an incident, so the model no longer has
to be right every time — only often enough that the retry budget holds. Same
invocations, same tokens, an order of magnitude less per token.

The drop is only as wide as the verifier's proof boundary. Whatever the verifier
contract's **Verifier does not prove** line names is still carried by the model
alone, and that residue sets the tier. A schema check against a semantic harm
buys no tier reduction on the semantic part of the judgment; it buys a HUMAN
post-pass gate instead. That one line of the contract is doing two jobs: it sets
the gate, and it sets the tier.

The converse is the more common finding. A step whose errors escape unverified
argues for the strongest tier available — and should be read as evidence that
the design is missing a verifier rather than a model. Of the two fixes, the
stronger model is the expensive one and the weaker one: it lowers the error rate
and pays for that every invocation, while the verifier changes what an error
costs and is paid for once.

## Default posture

**Start at the weakest tier that could work and move up when a named failure
forces it.** Not the reverse. Starting at the strongest and never revisiting is
the same error as reaching for an agent loop without asking whether a pipeline
would do: defensible in the moment, invisible afterwards, and paid for every day
the system runs.

A move up needs a named failure — a sample where the weaker tier was wrong, an
error the verifier let through, a specific objection from a reviewer who read
the output. "To be safe" is not a failure, and neither is a preference for the
model the author happens to use. The failure that would force the move belongs
in the verdict's revisit-when section, where it can be checked against reality
later.

## Boundary cases

- Extracting twelve fields from an invoice is WEAK at ten invoices a day and
  WEAK at a million. Volume raises the stakes of the tier choice; it does not
  raise the tier.
- Choosing which of three subsystems a stack trace implicates is MID, not WEAK:
  the trace, the recent changes, and the service topology have to be reconciled,
  and nothing downstream disagrees with the answer.
- The same subsystem choice is WEAK in a system that reproduces the failure
  against each candidate before acting. The reproduction is the verifier, and it
  is what changed the tier — not the difficulty of the judgment, which is
  identical.
- Drafting a customer email that a named person sends is MID, and the send is
  HUMAN. The approver is not a verifier: someone who accepts nearly every draft
  is providing accountability, not a check, and the acceptance rate is the tell.
- A step that reads an entire repository to answer one narrow question is not
  STRONG because the repository is large. Put retrieval in front of it and
  re-ask the three questions against what the model actually receives.
