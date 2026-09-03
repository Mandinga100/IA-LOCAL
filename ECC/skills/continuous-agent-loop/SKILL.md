---
name: continuous-agent-loop
description: Patterns for continuous autonomous agent loops with quality gates, evals, and recovery controls.
metadata:
  origin: ECC
---

# Continuous Agent Loop

This is the v1.8+ canonical loop skill name. It supersedes `autonomous-loops` while keeping compatibility for one release.

## Loop Selection Flow

```text
Start
  |
  +-- Need strict CI/PR control? -- yes --> continuous-pr
  |
  +-- Need RFC decomposition? -- yes --> rfc-dag
  |
  +-- Need exploratory parallel generation? -- yes --> infinite
  |
  +-- default --> sequential
```

## Combined Pattern

Recommended production stack:
1. RFC decomposition (`ralphinho-rfc-pipeline`)
2. quality gates (`plankton-code-quality` + `/quality-gate`)
3. eval loop (`eval-harness`)
4. session persistence (`nanoclaw-repl`)

## Failure Modes

- loop churn without measurable progress
- repeated retries with same root cause
- merge queue stalls
- cost drift from unbounded escalation

## Recovery

- freeze loop
- run `/harness-audit`
- reduce scope to failing unit
- replay with explicit acceptance criteria

## Unattended / Scheduled Runs

Any loop pattern here (`sequential`, `continuous-pr`, `rfc-dag`, `infinite`,
or a `benchmark-optimization-loop` / `gan-style-harness` cycle) can run
overnight or on a cron instead of in a live session. This is a scheduling
concern, not a new loop pattern — do not build a bespoke skill per domain
just to get "run it while I sleep, summarize in the morning." Wire the
existing pieces instead:

1. Confirm the loop already satisfies every item in the `loop-operator`
   agent's "Required Checks" (quality gates active, eval baseline
   exists, rollback path exists, worktree/branch isolation configured)
   — a loop that isn't safe supervised is not safe unattended.
2. Register the run with `mcp__scheduled-tasks__create_scheduled_task`,
   pointing the prompt at the loop's entry command (e.g. `/loop-start`,
   `/project:gan-build`, or a `benchmark-optimization-loop` invocation)
   plus explicit stop conditions (`--max-runs`, `--max-cost`,
   `--max-duration`, or a completion signal).
3. On completion, write the run's ledger/variant-table/eviction-context
   to a durable file, then render it as a summary the same way the
   `morning` skill renders a daily brief — one artifact or message
   waiting when the human checks back in, not a raw log to scroll.
4. Never widen scheduled-run permissions past what the interactive
   version of the same loop already had. Scheduling should not be used
   as a backdoor to grant a loop capabilities a human wouldn't approve
   in the room.

This is the generalized version of the "wake up to a log and a better
result" pattern popularized by single-purpose research-loop repos
(e.g. fixed-wall-clock-budget training loops): the interesting part is
the loop discipline above, not the domain it's applied to. Any loop that
already meets the Required Checks gets this for free — it does not need
a domain-specific rebuild.
