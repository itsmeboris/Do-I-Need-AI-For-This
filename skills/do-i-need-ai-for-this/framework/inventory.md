# Inventory

The frame describes one automation. A repository is often not one automation.
Point the eight slots at a target holding twenty of them and they resolve to one
of two useless things: a description of the dispatcher alone, or an average that
is true of nothing actually running. Two agents in the same repository can differ
by every slot that matters — one renders a diagram into a scratch folder, the
other writes to a system other people read.

This step runs before the frame in audit mode. It answers one question, and the
answer bounds everything after it: what separate things are in here, and which of
them is this audit actually going to cover?

## What a unit is

A **unit** is one automation with its own trigger and its own blast radius.

**Test:** name what starts it, and name what is different in the world when it
finishes wrong. Two candidates are the same unit when both answers match. They
are different units when either answer differs.

Both halves are needed. Trigger alone splits a single automation into as many
units as it has command-line flags. Blast radius alone merges a scheduled job and
a hand-run script that happen to write the same file, when the thing worth knowing
is that one of them runs unattended.

## Grouping rules

Apply these to every candidate the enumeration turns up.

- **One dispatchable module is usually one unit.** If the dispatcher can run it
  by itself and it produces its own output, it is a unit.
- **A shared base class, helper, client wrapper, or data model is not a unit.**
  It has no trigger of its own; it runs when its caller runs. Its cost belongs to
  the callers, and giving it a row of its own double-counts every invocation.
- **The dispatcher is a unit.** Choosing which unit runs, in what order, and
  whether to run one a second time is judgment, and it carries a blast radius no
  single dispatched unit has: a re-dispatch loop can spend the entire run's
  budget without any one unit misbehaving. Audit it as a unit, not as scaffolding
  around the others.
- **A worker the parent spawns per item is part of the parent's unit.** Its
  trigger is the parent's dispatch decision, not an event of its own. Record the
  fan-out in the parent's spend instead — that is where it lands on the bill.
- **Two entry points over the same code with the same blast radius are one unit
  with two triggers.** Name both triggers in the row rather than splitting the
  row; the architecture question is the same for both.
- **A unit does not have to be source code.** A command definition, a skill file,
  a scheduled job, or a CI step is a unit when it carries its own trigger and its
  own blast radius. Prompt files that instruct a model to go and check things are
  units, and they are the ones an inventory drawn from the source tree misses.
- **A candidate with no observable action is not a unit.** If nothing outside the
  process differs after it runs, there is nothing for a blast radius to describe.

## Finding the units

Look for a declared list first. A registry, a dispatch table, a plugin manifest,
a job schedule — anything the target maintains that names its own components. A
module registry listing every agent with a version and a one-line description
saves an hour of reading, and it is worth ten minutes to look for one.

It is never the whole inventory. A declared list contains what its author thought
of as a component, which is why the dispatch table it feeds is the first thing to
check it against, and why the second thing is to look where it does not: command
and skill definitions, scheduled entries, CI steps, modules with a `__main__`.

Record where you looked, not only what you found. A coverage claim is worth
exactly as much as the enumeration behind it, and a reader cannot tell a thorough
sweep from a lucky one unless the sweep is written down.

## When multi-unit mode applies

Multi-unit mode engages when the target has **more than one distinct (trigger,
blast radius) pair**.

That is the whole rule. Not a file count and not a line count: a forty-file
package with one entry point and one output is a single unit, and three scheduled
jobs declared in one file are three units. Count the pairs.

The rule is the output of the enumeration, not a precondition for it. You cannot
know how many distinct pairs a target has until you have looked, so enumerate
first and decide after. When the count comes back one, drop the inventory and
audit as normal — the ordinary frame is correct, and the inventory and unit-verdict
sections are omitted from the verdict entirely rather than left empty.

## Ranking

Rank by **model spend × blast radius**. Ranking decides audit order, and audit
order matters because the audit stops before the end of the list. What gets
dropped should be what is cheapest and least dangerous, not what happens to sort
last alphabetically.

Score each axis from 1 to 4 using what the source shows.

**Model spend (S)** — invocations per run times tokens per invocation.

| S | what the source shows |
| --- | --- |
| 1 | no model invocation at all |
| 2 | one model call under a small turn cap, roughly ten or fewer |
| 3 | one model call under a larger cap, or a fixed handful of calls |
| 4 | calls scale with the input: a per-item worker, a retry cascade, an uncapped loop |

Read the cap from the call site that sets it. A turn cap is a ceiling, not a
measurement — a unit capped at 40 turns may average 6. Write it as the ceiling it
is, and label it accordingly when reporting operational evidence. For tokens per
invocation, read what the prompt pulls in: one record, one log, or a whole tree.

**Blast radius (R)** — reversibility and whether the action escapes the process.

| R | what the action does |
| --- | --- |
| 1 | returns a value to its caller; nothing outside the process changes |
| 2 | writes only inside the run's own output directory, reversible by deleting it |
| 3 | writes outside that directory, on a system you control and can restore |
| 4 | escapes the process: a network write, a remote mutation, or a message a person will act on |

The rank score is `S × R`, from 1 to 16. Break ties by the higher S, because
spend is the part an architecture change can remove.

Both scales start at 1 rather than 0 deliberately. A unit that invokes no model
still belongs in the ordering: with a zero, a deterministic component that mutates
a remote checkout would sort below an in-process helper, and the list a reader
scans from the top would be ordered by something other than what deserves
attention first.

## Depth

Fully audit the highest-ranked five to eight units by default.

Depth is the caller's decision, not this framework's. Present the ranked
inventory and the intended depth together, before the expensive part begins, and
accept any of: named units, everything above a rank score, or all of them. This
framework imposes no budget. A caller that has one enforces it and says so in the
verdict, because a cut made for budget is a different fact than a cut made for
rank.

## Accounting

Every unit in the inventory appears exactly once in one of two places: as a unit
verdict, or in the not-audited list with the reason it was skipped. There is no
third place, and silence is not one of them.

This is the rule the step exists for. A verdict that inventories twenty-seven
units, audits six, and says nothing about the other twenty-one reads as a verdict
on the repository. It is a verdict on six twenty-sevenths of it. An overstated
coverage claim is worse than no verdict at all: a reader without a verdict knows
they still have to look, and a reader holding this one believes they do not.

Give each skipped unit a specific reason. "Rank 2, below the depth cut of 8" is a
reason. "Out of scope" is not — it restates the omission as though it were an
explanation. `check_verdict.py` enforces the reconciliation, so a verdict that
drops a unit fails the gate rather than shipping quietly.
