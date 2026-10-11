# Question Bank

## Trigger

- What has to happen for this to run at all?
- Is there something that already knows when that happens — a webhook, a queue, a notification, an exit code?
- If you did this by hand today, what would tell you it was time?
- Would running it on a fixed schedule instead of on the event break anything?

## Cadence and volume

- How often does the trigger fire in a typical day or week?
- How many items arrive in a single run — one, dozens, or potentially thousands?
- Is there a burst pattern, or is the volume roughly steady?
- If volume grows tenfold, does the architecture you have in mind still hold up?

## Inputs

- What information does the system hand to this automation when it starts?
- Is that information complete enough to make the decision, or does something need to be looked up first?
- Where does each input come from, and is it available at trigger time or fetched on demand?
- Is any of the input sensitive in a way that affects where it can be processed?

## Decision

- What choice does the automation have to make, and for whom?
- Write down the rule you would follow to make this choice. If you can finish that sentence, it is not a judgment call.
- Are there cases where the rule breaks down — inputs where a human would pause and weigh competing factors?
- If the automation gets it wrong, how obvious is that and how quickly?

## Action and blast radius

- What does the automation actually do when it has made its decision?
- Can that action be undone, or is it permanent?
- What is the worst realistic outcome if the automation acts incorrectly?
- Does the action touch one item at a time, or can a single run affect many?

## Success signal

- How does the automation know it did the right thing?
- Does the target system expose any state change, metric, or confirmation you can observe?
- If the automation ran silently for a week and produced wrong results, how would you find out?
- Is there a downstream effect that could serve as a lagging success indicator?

## Tolerance and review

- How many errors per hundred runs are acceptable before someone needs to intervene?
- Who reviews the automation's decisions, and how do they access them?
- Can a human override or roll back a decision after the fact?
- Is the tolerance different for false positives versus false negatives?

## Constraints

- Is there a latency requirement — does this need to complete in seconds, minutes, or is batch fine?
- Are there cost limits per run or per month that rule out expensive model calls?
- Does any input contain data that cannot leave a particular environment or jurisdiction?
- Are there existing systems this must integrate with that constrain the implementation choices?
- Is there a compliance or audit requirement that affects how decisions are logged?
