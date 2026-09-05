---
name: codebase-graph-memory
description: Persistent code knowledge graph via codebase-memory-mcp (tree-sitter + Hybrid LSP). Index a repo once, then answer structural questions — who calls what, blast radius of a diff, dead code, architecture overview — from a saved graph instead of re-grepping. Use for large or unfamiliar codebases where repeated file-by-file exploration is expensive. Opt-in external MCP; not auto-enabled.
metadata:
  origin: community
---

# Codebase Graph Memory (codebase-memory-mcp)

Structural code intelligence for large repos. Builds a **persistent knowledge graph** of a codebase (functions, classes, call chains, imports, HTTP routes, cross-service links) with [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parsing plus a bundled type-resolution layer, and answers structural queries against that graph instead of re-scanning files each time.

**Upstream:** [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)
**Distribution:** single static binary (C), SQLite-backed, 100% local, no telemetry.

## Why this exists (vs what ECC already has)

ECC's `codebase-onboarding` and `repo-scan` do a fresh Glob/Grep sweep every time — nothing persists, and structural facts (who calls this function across files/packages, what a diff breaks, what code is dead) get recomputed from scratch on every question. On a large or legacy repo that is slow and token-heavy. This skill wraps an external server that indexes once and then answers those questions from a saved graph in milliseconds.

Use it when the repo is big enough that the *persistence* matters. On small or short-lived repos, `codebase-onboarding` is lighter and has no external dependency — prefer it there.

## Security and boundaries

**Opt-in (ECC):** The `codebase-memory` block in `mcp-configs/mcp-servers.json` is a template only. ECC plugin installs never auto-enable bundled MCP servers. Copy the entry into your own config only if you want it. Exclude it during ECC install/sync with `ECC_DISABLED_MCPS=codebase-memory,...`.

**Do NOT use the vendor's auto-installer.** The upstream `install.sh` / `install.ps1` self-configures up to 43 client surfaces, writes global lifecycle hooks, and creates subagents across your whole system. That directly conflicts with the ECC constraint *"no arbitrary external runtime installs in shipped ECC surfaces"* (`WORKING-CONTEXT.md`). Instead:

1. Download the binary manually from the [signed releases](https://github.com/DeusData/codebase-memory-mcp/releases/latest), or build from source, and **verify the SLSA provenance and SHA-256 checksum yourself** before trusting it. VirusTotal/SLSA prove the binary is not malware; they do not prove it does only what the README claims. It is a compiled C binary, not line-auditable like ECC's Node hooks — treat it accordingly.
2. Register **only** the single stdio MCP entry (see below). Do not run the multi-client installer, do not let it write hooks or subagents.

**Keep it contained:**

- Set `CBM_ALLOWED_ROOT` to your project root so `index_repository` refuses paths outside it.
- Run `codebase-memory-mcp config set auto_watch false` to stop the background git-polling watcher from registering itself. ECC's persistence philosophy is local-by-default and explicitly gated (`hooks/memory-persistence/README.md`); a always-on background daemon per project is the opposite default and should stay off unless you deliberately want it.
- Indexes persist to `~/.cache/codebase-memory-mcp/`. Do not index repos containing secrets you would not want in that local cache. Reset with `rm -rf ~/.cache/codebase-memory-mcp/`.

**If the MCP is unavailable (not installed, crashed, not indexed):** Do not invent graph results, call chains, or "no callers found" conclusions. Tell the user the graph was unavailable and fall back to `codebase-onboarding` / Grep / Glob. A missing graph is not evidence of absence.

## When to Use

- Large, unfamiliar, or legacy codebase where "who calls X" / "what breaks if I change Y" would take many grep+read cycles
- Repeated structural questions across a session or across sessions on the same repo
- Impact analysis of a diff before a risky change (`detect_changes`)
- Dead-code discovery via the call graph
- Cross-file / cross-package / cross-service call tracing that plain grep cannot resolve (imports, inheritance, type-inferred calls)

## When NOT to Use

| Instead of this skill | Use |
|---|---|
| First-pass orientation on a new repo, generate a CLAUDE.md | `codebase-onboarding` |
| Ownership / third-party / dead-weight audit of source assets | `repo-scan` |
| Recording an architectural decision durably | `architecture-decision-records` (see overlap note below) |
| A guided, human-readable walkthrough artifact | `code-tour` |
| Structural maintainability / Code Health regression gating | `codehealth-mcp` |
| Small repo, one-off question | Grep / Glob directly — no external server needed |

## Overlap to resolve before enabling

This server ships tools that overlap existing ECC surfaces. Decide the source of truth up front so you do not create a fourth way to do the same thing:

- **`manage_adr` (server) vs `architecture-decision-records` (ECC skill):** Keep ECC's `architecture-decision-records` as the source of truth for ADRs. Treat the server's `manage_adr` as read-only convenience at most; do not split ADRs across two stores.
- **`get_architecture` (server) vs `codebase-onboarding` Phase 1-2:** Use `get_architecture` for a fast machine overview on an already-indexed large repo; use `codebase-onboarding` when the deliverable is a human onboarding guide or CLAUDE.md. Do not run both and reconcile by hand.

## How It Works

### 1. Install the binary manually and register the MCP entry

Copy the `codebase-memory` entry from `mcp-configs/mcp-servers.json` into your harness config.

**Claude Code** (`~/.claude.json` → `mcpServers`), pointing `command` at the binary you installed and verified:

```json
"codebase-memory": {
  "command": "/absolute/path/to/codebase-memory-mcp",
  "args": [],
  "env": { "CBM_ALLOWED_ROOT": "/absolute/path/to/your/project" }
}
```

**Project-scoped:** merge the same block into `.mcp.json` at the repo root.

Then, once, disable the background watcher:

```bash
codebase-memory-mcp config set auto_watch false
```

Restart the session and confirm the `codebase-memory` server is connected (`/mcp`) before relying on it.

### 2. Index, then query

```
You: "Index this project"        → agent calls index_repository(repo_path="/abs/path")
You: "What calls ProcessOrder?"  → agent calls trace_path(function_name="ProcessOrder", direction="inbound")
```

The server has **no LLM** — it only executes graph queries and returns structured results. Your agent is the intelligence layer that turns your question into a tool call and the result into plain language.

### 3. Core tools

| Tool | When to use |
|------|-------------|
| `index_repository` | Build/refresh the graph for a repo. Run once; re-run after big changes if watcher is off. |
| `list_projects` | See indexed project names (needed as the `project` argument elsewhere). |
| `search_graph` | Find symbols by name pattern / label / file before tracing. Run this to get exact qualified names. |
| `trace_path` | Who calls a function and what it calls (BFS, depth 1-5). The main call-graph tool. |
| `detect_changes` | Map a git diff to affected symbols + blast radius with risk classification, before a risky change. |
| `get_architecture` | Fast overview: languages, packages, routes, hotspots, clusters. |
| `query_graph` | Read-only Cypher-like queries for custom traversals (e.g. dead code: `WHERE NOT EXISTS { (f)<-[:CALLS]-() }`). |
| `get_code_snippet` | Read source for a symbol by qualified name (discover the name with `search_graph` first). |

Prefer the narrowest tool that answers the question. For a single symbol, `search_graph` → `trace_path` is usually enough; reach for `query_graph` only when a standard tool cannot express the traversal.

## Pairing with ECC

| ECC skill / flow | Role of the graph |
|------------------|-------------------|
| `codebase-onboarding` | Human onboarding + CLAUDE.md; graph adds fast cross-file call tracing on large repos |
| `repo-scan` | Ownership/dead-weight audit; graph adds precise call-based dead-code detection |
| `code-tour` | Verify real anchors and call paths before writing tour steps |
| `verification-loop` / `/quality-gate` | Use `detect_changes` to size blast radius before declaring a change safe |
| `architecture-decision-records` | Source of truth for ADRs — do not duplicate into `manage_adr` |
| `mle-workflow` / `benchmark-optimization-loop` | Graph queries to locate hot paths before optimizing |

**Context tip:** ECC recommends keeping enabled MCP count low (< 10). Enable `codebase-memory` when working a large repo; disable it when not needed.

## Anti-Patterns

- Running the vendor's auto-installer instead of registering the single MCP entry manually.
- Leaving `auto_watch` on, so a background daemon indexes every project silently.
- Indexing a repo with secrets into the local cache without thinking about it.
- Trusting `trace_path` "no callers" as proof of dead code without confirming the graph is current (re-index or check `index_status` first) and that the caller isn't dynamic/reflection-based.
- Storing ADRs in both `manage_adr` and `architecture-decision-records`.
- Reporting graph results when the server was actually down — say it was unavailable instead.

## Related Skills

- `codebase-onboarding` — first-pass repo understanding, no external dependency
- `repo-scan` — cross-stack asset/ownership audit
- `code-tour` — guided walkthrough artifacts
- `architecture-decision-records` — durable ADRs (source of truth)
- `codehealth-mcp` — structural maintainability gating (same opt-in MCP pattern)
- `verification-loop` — build/test/lint gate
