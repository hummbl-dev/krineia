# KRINEIA — Receipt Schema v0.1

**Status**: DRAFT (2026-04-27)
**Authority**: This document specifies the receipt format emitted by KRINEIA and consumed by `krineia-mcp`. Receipts that do not validate against this schema are not KRINEIA receipts.

---

## 0. Why this exists

KRINEIA is the append-only sovereignty layer of the HUMMBL stack. A KRINEIA **receipt** is the atomic governance record that proves a decision happened: who, when, in what state, with what deviation from setpoint, cryptographically chained to everything that came before.

Receipts are **not** generic logs. They are post-mortem-only audit artifacts that NEVER feed back into any agent's reward, gradient, or policy-update path. Agents may read the chain for coordination; agents may not learn from it.

For the five governing invariants, see `INVARIANTS.md`.

---

## 1. Receipt envelope

Each receipt is a single JSON object on a single line of a JSON-Lines (`.jsonl`) file. All receipts have exactly six top-level fields:

| Field | Type | Description |
|---|---|---|
| `id` | string (UUIDv4) | Globally unique identifier for this receipt |
| `time` | string (ISO 8601 UTC, `Z` suffix) | When the event happened |
| `state` | object | Structured event state (see §3) |
| `drift` | number \| null | Deviation from setpoint (null when not measured) |
| `prev_hash` | string (64 hex) | SHA-256 hash of the prior receipt's canonical form |
| `hash` | string (64 hex) | SHA-256 hash of THIS receipt's canonical form |

The first five fields map 1:1 to the KRINEIA 4-field model (`id`, `time`, `state`, `drift`) plus the chain link (`prev_hash`). The `hash` field closes the chain forward.

### Example (genesis receipt)

```json
{"id":"90569814-c21b-43af-9f9b-825e722b9377","time":"2026-04-27T09:36:10Z","state":{"event":"daemon.start","payload":{"pid":27860,"args":{"once":true,"max_topics":0}}},"drift":null,"prev_hash":"0000000000000000000000000000000000000000000000000000000000000000","hash":"bda150122731e1b697b269802bd37c4d57a87cf7495f959d824690c4fbdcfab3"}
```

---

## 2. Hash chain rule

### Canonicalization

The hash of a receipt is the SHA-256 of its **canonical form**, defined as:

```python
canonical = json.dumps(
    {"id": id, "time": time, "state": state, "drift": drift, "prev_hash": prev_hash},
    sort_keys=True,
    separators=(",", ":"),
)
hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

Three rules to note:
1. The `hash` field itself is **not** part of the canonical form.
2. `sort_keys=True` sorts keys recursively at every depth — payloads must be deterministically serializable.
3. `separators=(",", ":")` strips whitespace — no pretty-printing in the canonical form.

### Genesis

The first receipt in any chain has `prev_hash` = `"0" * 64` (sixty-four ASCII zeros).

### Linkage

For every subsequent receipt at index `i`, `prev_hash[i] == hash[i-1]`.

### Validation algorithm

A chain is valid iff:
- The first receipt has `prev_hash == "0" * 64`.
- For every adjacent pair `(prev, curr)`, `curr.prev_hash == prev.hash`.
- For every receipt, `hash == sha256(canonical_form_without_hash_field)`.

A break at any point means the chain is forked, tampered, or truncated.

---

## 3. Event taxonomy

Receipts come from two trace levels, depending on which process emitted them. Every event below was enumerated against the v0.1 reference implementation; payload keys are exhaustive (no silent fields).

### 3.1 Daemon-level (`krineia_daemon_trace.jsonl`)

Emitted by the long-running daemon. One file per daemon installation. **14 event types.**

| Event | Payload keys | Trigger |
|---|---|---|
| `daemon.start` | `pid`, `args` | Daemon process boot |
| `daemon.ollama_unreachable_at_start` | *(empty)* | Boot-time Ollama probe failed |
| `daemon.heartbeat` | `pending`, `done`, `failed`, `topics_processed_this_run`, `current_backoff_s` | 15-min idle heartbeat (no topic in progress) |
| `daemon.stale_lock_reclaimed` | `prior_pid`, `prior_start` | Found a dead daemon's lock file at boot, took it over |
| `daemon.stop_requested` | `topics_processed_this_run` | SIGTERM/SIGINT received |
| `daemon.fatal` | `error_type`, `error` | Unhandled exception in main loop |
| `daemon.stop` | `topics_processed_this_run` | Daemon final exit (always emitted, even after fatal) |
| `queue.reclaim_stale` | `file` | A topic was sitting in `in_progress/` from a prior dead daemon, moved back to `pending/` |
| `topic.claim` | `topic_id`, `run_id`, `topic`, `submitted_by`, `priority` | Daemon claimed a pending topic |
| `topic.bad_json` | `file`, `error` | Pending file failed to parse — moved straight to `failed/` |
| `topic.empty` | `file`, `topic_id` | Pending file had no `topic` field — moved to `failed/` |
| `topic.complete` | `topic_id`, `run_id`, `elapsed_s` | Orchestrator subprocess returned exit 0 |
| `topic.fail` | `topic_id`, `run_id`, `exit_code`, `elapsed_s` | Orchestrator subprocess returned non-zero |
| `topic.timeout` | `topic_id`, `run_id`, `elapsed_s` | Orchestrator subprocess exceeded `ORCHESTRATOR_TIMEOUT` (default 7200s) |

### 3.2 Orchestrator-level (`<run_dir>/krineia_trace.jsonl`)

Emitted by `nodezero_orchestrator.py` once per topic run. One file per run dir. **18 event types.**

| Event | Payload keys | Trigger |
|---|---|---|
| `orchestrator.start` | `run_id`, `run_dir`, `mode`, `topic_arg`, `topics_file` | Orchestrator entry point |
| `topic.start` | `topic_idx`, `slug`, `topic`, `lenses_planned` | Begin processing a topic |
| `lens.start` | `module`, `lens_id`, `topic_slug`, `model` | Begin a lens generation |
| `lens.ok` | `module`, `lens_id`, `topic_slug`, `out_size`, `elapsed_s` | Lens completed |
| `lens.fail` | `module`, `lens_id`, `topic_slug`, `elapsed_s` | Lens model call errored |
| `lens.skip_cached` | `module`, `lens_id`, `topic_slug`, `out_size` | Lens output existed on disk, skipped re-generation |
| `lens.missing_in_registry` | `module`, `lens_id`, `topic_slug` | Planned lens not in registry — skipped |
| `synthesis.start` | `topic_slug`, `model`, `lens_inputs` | Begin synthesis generation |
| `synthesis.ok` | `topic_slug`, `out_size`, `elapsed_s` | Synthesis completed |
| `synthesis.fail` | `topic_slug`, `elapsed_s` | Synthesis model call errored |
| `synthesis.skip_cached` | `topic_slug` | Synthesis output existed, skipped |
| `paideia.start` | `topic_slug`, `model` | Begin PAIDEIA-9 scoring |
| `paideia.ok` | `topic_slug`, `signature`, `scores` | Score completed; scores object has 9 axis keys (M, D, E, V, C, L, S, P, A) |
| `paideia.ok_raw` | `topic_slug` | Scoring returned raw (unparsed) text — partial success |
| `paideia.fail` | `topic_slug` | Score model call errored |
| `paideia.skip_no_synth` | `topic_slug` | Synthesis missing — skipped scoring |
| `topic.complete` | `topic_idx`, `slug` | All lenses + synthesis + score done |
| `orchestrator.complete` | `run_id`, `counters`, `sitrep_path` | Orchestrator final exit |

### 3.3 Chain semantics

The two trace levels are **independent chains**. The daemon trace chains daemon events; each per-run trace chains its own orchestrator events. They are linked at the **data layer** via shared `run_id` and `topic_id`, not at the **hash layer**.

A future spec may unify them under a single Merkle root (Phase 2).

### 3.4 Conventions

- **Skip events** (`*.skip_cached`, `*.skip_no_synth`) are part of the chain even though no model work was done — they record the cache-hit decision for audit.
- **Fail events** (`*.fail`, `topic.fail`, `topic.timeout`, `topic.bad_json`, `topic.empty`, `daemon.fatal`) record state transitions, NOT error details. Stack traces / stderr go to plain-text logs (`orchestrator.log`, `krineia_daemon.log`) and the per-topic FAILED envelope (§5), not into the chain. Rationale: receipts are governance artifacts, not debugging aids; keeping them small and structurally stable matters more than capturing every byte of an error.

---

## 4. Per-topic outputs

When a topic completes, the run dir at `<run_dir>/<slug>/` contains:

| File | Purpose |
|---|---|
| `_meta.json` | Topic, slug, lenses attempted, completion timestamp |
| `<module>__<lens_id>.md` | Raw model output for each lens (one file per lens) |
| `synthesis.md` | Cross-lens synthesis (the model's converged answer) |
| `paideia_score.json` | PAIDEIA-9 9-axis content quality score |

The run-level files are:

| File | Purpose |
|---|---|
| `krineia_trace.jsonl` | Per-run hash chain (§3.2) |
| `lenses_used.json` | Final lens roster after rotation |
| `topics.json` | Topic list as input to this run |
| `orchestrator.log` | Plain-text human-readable log |
| `SITREP.md` | Generated summary report |

---

## 5. Per-topic envelope

When a topic is processed end-to-end, the input envelope at `queue/pending/<id>.json` is moved to `queue/done/<id>.json` (or `queue/failed/<id>.json`) with completion metadata appended:

| Field | Source | Description |
|---|---|---|
| `id` | submitter | 8-hex slug; primary topic key |
| `topic` | submitter | The question text |
| `submitted_utc` | submitter | When the topic was queued |
| `submitted_by` | submitter | Actor identifier |
| `priority` | submitter | Integer priority (higher = sooner) |
| `_completed_utc` | daemon | When orchestrator returned |
| `_run_id` | daemon | Run dir slug (used to find outputs) |
| `_run_dir` | daemon | Absolute path to run dir |
| `_exit_code` | daemon | Orchestrator subprocess exit code |
| `_elapsed_s` | daemon | Wall time of orchestrator subprocess |

Underscore-prefixed fields are appended by the daemon and were not present at submission time.

---

## 6. Phase 2 extensions (not yet emitted)

The first canonical run (topic: "What receipt fields must KRINEIA emit to be MCP-tool-callable as krineia-mcp?", run_id `20260427-093612-0c874676`) recommended four additional fields for future receipts. These are **NOT** part of v0.1 — they are tracked here for v0.2 design:

| Field | Source lens | Purpose |
|---|---|---|
| `intent_hash` | poiesis-seed | SHA-256 over the formal intent description prior to tool execution |
| `authorization_level` | praxis-mond | Verifiable claim about who authorized the call (reads governance bus / IDP) |
| `scope_constraints` | poiesis-seed | Explicit list of scopes the call is bounded to |
| `epistemic_redactions` | praxis-mond | Log of confidence scores + redaction rationales (with privacy controls per praxis-aurelius) |

The aurelius lens raised a tension worth resolving in v0.2: exhaustive epistemic transparency vs. exposing sensitive confidence data to adversarial exploitation. v0.2 design must answer it.

---

## 7. Reference implementations

The v0.1 schema is emitted by:

- `krineia_daemon.py` — daemon-level chain (§3.1). KRINEIATrace class, lines 100-135.
- `nodezero_orchestrator.py` — per-run chain (§3.2).

Canonicalization function lives at `krineia_daemon.py:129-130`.

The standalone validator lives at `tools/verify_chain.py`.

---

## 8. Versioning

- **v0.1** (2026-04-27) — initial spec, captures emitted format end-to-end.
- **v0.2** (planned) — Phase 2 extensions (§6); two-chain unification (§3.3).
- **v1.0** (target) — frozen schema for the May 15 LOI gate.

Changes between v0.x versions are additive. Breaking changes require a SemVer major bump and an ADR explaining why.

---

## 9. Source receipt

This v0.1 schema was derived from a single end-to-end KRINEIA daemon run on 2026-04-27, run_id `20260427-093612-0c874676`. The daemon trace, per-run trace, and outputs are reproducible by re-running the same topic against the same daemon code.

The daemon code at the time of derivation:
- `krineia_daemon.py` — committed locally at `C:/Users/Owner/overnight/krineia_daemon.py`, sha will land in repo on first commit
- `nodezero_orchestrator.py` — same path

Once committed to this repo, the canonical paths become `daemon/krineia_daemon.py` and `daemon/nodezero_orchestrator.py` (Phase 2 reorganization).
