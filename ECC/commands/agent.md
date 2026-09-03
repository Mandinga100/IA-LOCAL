---
description: Invoke any agent by name with an optional task description. Lists available agents when called without arguments.
argument-hint: name=<agent-name> [task="<description>"]
---

# Agent Command

Bridges the user to any specialist agent in the catalog. Accepts a target agent name and an optional task description.

## Usage

**List available agents:**
```
/agent
```
→ Shows all 67 agents grouped by category (from CATALOG.md).

**Invoke a specific agent:**
```
/agent name=architect task="Design auth system for the API gateway"
```

**Invoke with task only (AI infers best agent):**
```
/agent task="Review this PR for security vulnerabilities"
```
→ Automatically routes to the best-matching agent.

## How It Works

1. If `name=` is provided, look up `agents/<name>.md`
2. If `name=` is absent, analyze `task=` and select the best-matching agent
3. If neither `name=` nor `task=` is provided, list all agents from CATALOG.md
4. Load the agent file and delegate execution with the task context

## Available Agents

Full taxonomy with all 67 agents and their categories: `CATALOG.md`

Quick reference by category:

| Category | Agents |
|---|---|
| review | code-reviewer, cpp-reviewer, csharp-reviewer, database-reviewer, django-reviewer, fastapi-reviewer, flutter-reviewer, fsharp-reviewer, go-reviewer, healthcare-reviewer, java-reviewer, kotlin-reviewer, mle-reviewer, network-config-reviewer, php-reviewer, python-reviewer, react-reviewer, rust-reviewer, security-reviewer, swift-reviewer, typescript-reviewer, vue-reviewer |
| architecture | a11y-architect, architect, code-architect, homelab-architect, network-architect |
| build | build-error-resolver, cpp-build-resolver, dart-build-resolver, django-build-resolver, go-build-resolver, harmonyos-app-resolver, java-build-resolver, kotlin-build-resolver, pytorch-build-resolver, react-build-resolver, rust-build-resolver, swift-build-resolver |
| planning | planner, spec-miner, tdd-guide |
| testing | e2e-runner, pr-test-analyzer |
| security | silent-failure-hunter |
| analysis | code-explorer, code-simplifier, comment-analyzer, conversation-analyzer, gan-planner, refactor-cleaner, type-design-analyzer |
| ops | agent-evaluator, chief-of-staff, doc-updater, docs-lookup, harness-optimizer, loop-operator, performance-optimizer |
| opensource | opensource-forker, opensource-packager, opensource-sanitizer |
| domain | gan-evaluator, gan-generator, marketing-agent, network-troubleshooter, seo-specialist |

## Links

- Full catalog: `CATALOG.md`
- Agents: `agents/`
