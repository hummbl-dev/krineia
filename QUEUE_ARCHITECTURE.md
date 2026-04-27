# Queue Architecture v0.1

*Design for the topic-research queue that drives canonical content generation in Verum.*

**Status**: v0.1 — DRAFT (2026-04-27)

## Why this document exists

Verum is a specification project. Specifications come from research questions answered well. Rather than write specs by hand from a single perspective, the Verum project uses a **multi-perspective synthesis pipeline** — each research question is processed by 6 lenses (3 ARCANA + 2 PRAXIS + 1 POIESIS), then synthesized, then scored on PAIDEIA-9 axes.

The pipeline runs continuously. To stay productive without operator intervention, it needs a **queue filler** — a component that watches the pending queue and generates new research questions when the queue dips below a threshold.

This document specifies how the queue filler stays governed and how it stays relevant to ongoing work.

## High-level architecture

```
                   intent.md         CLP ledger.jsonl       Bus messages.tsv
                   (current focus)   (recent discoveries)   (BLOCKED, PROPOSALs)
                         \                    |                    /
                          \                   |                   /
                           \                  ↓                  /
                            →→→  Queue Filler (theme + signals)  ←  themes/<slug>.json
                                         ↓
                                  submit_topic.py
                                         ↓
                                  queue/pending/
                                         ↓
                                  Verum daemon (emits chain)
                                         ↓
                                  synthesis.md (Open Question sections)
                                         ↓                       ↑
                                         ↓                       |
                                   CLP ingest  ─→  feeds back into intent + ledger
                                   Bus STATUS  ─→  visible to other agents
                                   Verum trace ─→  governance receipt for the topic itself
```

The pipeline is a **closed loop**: outputs of one round feed inputs of the next. Done well, this is a slow form of recursive self-improvement on the question pool itself.

## Inputs

The queue filler conditions topic generation on four signals.

### 1. Theme files (`themes/<slug>.json`)

Each theme is a JSON file with three fields:

```json
{
  "name": "<slug>",
  "context": "<1-3 paragraph project description for the model>",
  "categories": ["category 1", "category 2", ...]
}
```

The `context` describes what's being built and what's canonical. The `categories` are sampled per generation batch so the topic stream stays diverse rather than collapsing onto one frame.

A **default theme** (`general-research`) is built into the filler for day-to-day operation. Project-specific themes live in `themes/`. Today's example: `themes/verum.json` for active Verum work.

### 2. Operator intent (`intent.md`)

The operator maintains an `intent.md` file that captures what they're currently working on, what gates are coming, what's blocked. The filler reads the current intent before each generation and includes the relevant excerpts in the model prompt. Topics that align with current intent stay strategic.

### 3. Cognitive ledger (`ledger.jsonl`)

The Cognitive Ledger Protocol (CLP) is an append-only JSONL log of discoveries, decisions, and lessons. The filler reads the last N entries (default 20) and includes their summaries in the prompt as "recent discoveries to build on." Topics that follow up on recent discoveries compound knowledge rather than scatter it.

### 4. Coordination bus (`messages.tsv`)

The multi-agent coordination bus is an append-only TSV log of inter-agent messages. The filler reads the last N (default 10) and includes any BLOCKED messages or pending PROPOSALs in the prompt. Topics that resolve open BLOCKED states are high-leverage.

### 5. Prior topics (already in the queue)

The filler also reads the topics already in `queue/pending/`, `queue/in_progress/`, and `queue/done/` (newest first, capped at 30). These are sent to the model with a "DO NOT REPEAT" instruction. This is the only one of the five signals that's been live since v0.1.

## Theme model

Themes are slug-keyed JSON files. The slug is an internal identifier, not a user-facing brand. It's used in:

- `--theme <slug>` CLI argument
- Submitted topic envelopes (sender field): `queue_filler/<slug>`
- Bus messages (when wired): `queue_filler/<slug>` as the `from` identity

Themes are version-controlled. Edits go through git like any other code change. Theme switches are recorded as a bus DECISION (operator-only) so the audit trail captures when focus shifts.

A **theme freshness loop** (planned in v0.5) periodically asks the model "given recent topics + current intent + ledger highlights, which categories should this theme rotate through next?" and rewrites the theme JSON. This keeps themes from going stale without operator hand-editing.

## Governance posture

The filler is itself an agent in the system, so it follows the same governance rules as other agents:

| Rule | Implementation |
|---|---|
| Canonical sender identity | `queue_filler/<theme-slug>` (separates from human submissions) |
| Lower-than-human priority | Submitted at priority 3 (human-submitted topics default to 5, preempting) |
| Auditable | Each generation event will write to a `queue_filler_trace.jsonl` chain (planned v0.3) |
| Visible | Each batch posts STATUS to the coordination bus (planned v0.3) |
| Killable | A `queue/PAUSE` sentinel file halts the filler (planned v0.2) |
| Theme-locked | A running filler is bound to a specific theme; switching themes requires restart |

## Roadmap

| Phase | Status | Adds |
|---|---|---|
| **v0.1** | Shipped 2026-04-27 | Theme JSON + LLM gen + queue-state-aware refill + dry-run mode |
| **v0.2** | Planned same day | Filler reads `intent.md` + last N CLP entries + last N bus messages as additional generation context. Adds `queue/PAUSE` sentinel for kill-switch. |
| **v0.3** | Planned | Filler emits its own VERUM trace (`queue_filler_trace.jsonl`). Posts STATUS to bus on each batch. Writes CLP entries per submission. |
| **v0.4** | Planned | Synthesis "Open Question" sections auto-extract → become next round's pending topics. Closes the loop between answer and next-question. |
| **v0.5** | Planned | Theme `categories` lists self-evolve from accumulated topic history + current intent. |

## Open questions for v0.2 design

- **Q1** How aggressively should bus BLOCKED context dominate generation? If too much, all topics become "how do we resolve BLOCKED X?" — useful for operations, but bad for theory questions. Suggest weighting: 1 of every N batches is "blocker-resolution focused", rest is theme-driven.
- **Q2** Should intent excerpts be summarized before injection, or pasted raw? Raw preserves nuance but bloats the prompt. Summarization adds another LLM call.
- **Q3** What does v0.3's VERUM trace canonicalize? Each topic submission as a `queue_filler.submit` event with hash chain — but the chain doesn't unify with the daemon-level chain or per-run chain. Three independent chains is starting to feel like overhead. Phase 2 unification (Merkle root) becomes more important.
- **Q4** Theme files in v0.5 self-evolve. Who reviews? Auto-write makes themes "agent-mutable" which has governance implications. Solution: theme-edit proposals get bus PROPOSAL → operator DECISION before commit.

## Theme switching as a governance event

Today, switching the active theme means restarting the filler with `--theme <new>`. Tomorrow's design should make this a tracked event:

1. Operator decides on new focus
2. Operator (or filler watcher) posts a bus DECISION: `theme.switch <old> → <new>`
3. Filler watches bus, sees DECISION, restarts itself on new theme
4. New theme's first batch carries a special tag in submitter field: `queue_filler/<new>/transition`

This makes theme history queryable from the bus, which is a governance audit primitive.

## What this is not

- **Not a planner.** The filler doesn't pick which research questions matter most. It generates a broad, diverse, theme-anchored stream and lets the operator (or future ranking layer) prune.
- **Not a substitute for operator-submitted topics.** Filler-generated topics run at priority 3; anything operator-submitted at priority 5+ preempts. The filler keeps the pipeline warm during quiet periods, not directs it.
- **Not domain-locked.** The default theme is general-research. Project-specific themes are explicit opt-ins. There's no implicit assumption that the filler is generating Verum-only topics — that was true on launch day because today's focus was Verum, not a property of the filler.

## Reference

- `RECEIPT_SCHEMA.md` — receipt format the daemon emits (used by Verum chains, not the queue filler chain)
- Daemon source: `verum_daemon.py`, `nodezero_orchestrator.py`, `submit_topic.py`, `queue_filler.py` (currently at `C:/Users/Owner/overnight/`; will move to `daemon/` after stabilization)
- Theme files: `themes/<slug>.json`
