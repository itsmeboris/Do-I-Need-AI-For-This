# Anti-patterns

These phrases appear in automation briefs when a key frame slot has not been
filled. Each one is a symptom, not a character flaw. Detections surface as flags
in the verdict's frame section -- they prompt the architect to fill the slot before
proposing an architecture, and they are never framed as scolding.

The table maps each phrase to the unfilled slot it reveals and to the question
that unlocks the real answer.

| phrase | what it usually means | correction |
| --- | --- | --- |
| watch / keep checking / monitor | a polling loop was assumed; the event source was not investigated | what actually changes when the condition is true? is there a notification channel? |
| let it figure out | success criteria are undefined; the success-signal slot is empty | what would a correct run produce that an incorrect run would not? fill the success-signal slot |
| give it access to everything | blast radius is unbounded; the action-and-blast-radius slot is empty | which systems does it write to? what is the worst-case mutation if it acts incorrectly? |
| so it learns over time | no feedback loop has been designed; training signal is unspecified | where would the ground-truth label come from? who generates it, and how quickly? |
| it should be smart about | a judgment call has not been decomposed; the decision slot holds an intention | which specific decision? can you describe an input where two competent people would disagree? |
