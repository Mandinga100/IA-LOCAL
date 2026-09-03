---
description: Start a managed autonomous loop pattern with safety defaults and explicit stop conditions.
---

# Loop Start Command

Start a managed autonomous loop pattern with safety defaults.

## Usage

`/loop-start [pattern] [--mode safe|fast]`

- `pattern`: `sequential`, `continuous-pr`, `rfc-dag`, `infinite`
- `--mode`:
  - `safe` (default): strict quality gates and checkpoints
  - `fast`: reduced gates for speed

## Flow

1. Confirm repository state and branch strategy.
2. Select loop pattern and model tier strategy.
3. Enable required hooks/profile for the chosen mode.
4. Create loop plan and write runbook under `.claude/plans/`.
5. Print commands to start and monitor the loop.

## Required Safety Checks

- Verify tests pass before first loop iteration.
- Ensure `ECC_HOOK_PROFILE` is not disabled globally.
- Ensure loop has explicit stop condition.

## Running Unattended

To run the selected pattern on a schedule instead of interactively, see
`continuous-agent-loop`'s "Unattended / Scheduled Runs" section — register
the loop entry command via `mcp__scheduled-tasks__create_scheduled_task`
with the same stop conditions used here, and route completion to a
summary artifact rather than a raw log. Do not grant the scheduled run
any permission the interactive loop didn't already have.

## Arguments

$ARGUMENTS:
- `<pattern>` optional (`sequential|continuous-pr|rfc-dag|infinite`)
- `--mode safe|fast` optional
