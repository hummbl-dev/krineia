# KRINEIA

*An open standard for append-only governance receipts. Maintained by [HUMMBL Research Institute](https://hummbl.io). Formerly "Verum" — renamed 2026-05-13 per namespace audit.*

> **KRINEIA** (Greek: κρινεία — judgment, discernment) — cryptographically chained, post-mortem-only governance receipts. Proves that a decision happened, by whom, in what state, with what deviation from setpoint. Agents may **read** the chain for coordination, but chain contents NEVER feed back into any agent's reward, gradient, or policy-update path.

## What's in this repo

| File | Status | Purpose |
|---|---|---|
| [`INVARIANTS.md`](INVARIANTS.md) | v1.0-rc2 | Five governing invariants for KRINEIA receipt chains |
| [`RECEIPT_SCHEMA.md`](RECEIPT_SCHEMA.md) | v0.1 | Canonical schema for receipts emitted by KRINEIA and consumed by `krineia-mcp` |
| [`QUEUE_ARCHITECTURE.md`](QUEUE_ARCHITECTURE.md) | v0.1 | Architecture for the topic-research queue that produces canonical content |
| [`tools/verify_chain.py`](tools/verify_chain.py) | v1.0 candidate | Standalone stdlib validator for JSONL receipt hash chains |
| `LICENSE` | Apache-2.0 | License (full text) |
| `README.md` | this file | What you're reading |

Remaining v0.1 → v1.0 work:

- `VALIDATOR.md` — algorithm + reference implementation for independent chain verification
- `MCP_INTERFACE.md` — `krineia-mcp` tool surface (Model Context Protocol)
- `daemon/` — reference daemon implementation (currently at `C:/Users/Owner/overnight/`, will move once stable)

## Why this exists

Most "AI governance" tooling treats audit logs as observability — a side channel that gets flushed, summarized, or eventually overwritten. KRINEIA makes the opposite bet: **the audit log is the governance**. If a tool call wasn't recorded with a verifiable hash chain back to a known-good genesis, no governance happened. Period.

The five invariants make this operational:

1. **Append-only** — the log only grows. No deletes, no mutations, ever.
2. **No reward-path self-reference** — log contents never enter any agent's reward, gradient, or training signal. (Reading for coordination is allowed; learning from the log is not.)
3. **Minimal operators** — exactly three: `append()`, `project()`, `cut()`. Anything more is leakage.
4. **External analysis only** — the log is post-mortem. External tools inspect; the system itself doesn't.
5. **Trust-root separation** — the observed agent does not write its own receipts or control the receipt-generation process.

These are NOT software-engineering conventions; they are the load-bearing properties that distinguish a governance proof from a self-referential optimization target.

## Status

**v0.1 — DRAFT.** Schema captures the format emitted by the v0.1 reference daemon. v1.0 will be frozen ahead of the first paid pilot deployment.

This repo is the **canonical** KRINEIA spec. The reference daemon, validator, and MCP interface are tracked here (or will move here) for SPDX-resolvable provenance.

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).

Receipt format and validator algorithm are intended to be implementable freely; "KRINEIA" the trademark / brand is not granted by this license.

## About the maintainer

**HUMMBL Research Institute** is a research institute incorporated as HUMMBL, LLC (Georgia, USA). The institute publishes open standards (like this one), and offers products, services, courses, and certifications building on its research.

The `hummbl-` prefix on GitHub repository paths is an organizational convention, not a product brand. Products published by the institute use their own names.

## Related research from HUMMBL

KRINEIA sits within a broader research stack at the institute:

- **KRINEIA (theory layer)** — the governing invariants codified in this implementation. The theory predates this repo and informs all sovereignty/audit design choices.
- **Base120 (mental models)** — 120 reasoning operators in 6 families. A KRINEIA receipt can record which Base120 operator drove a decision.
- **BKI (Belonging as Knowledge Infrastructure)** — belonging as the structural precondition for knowledge creation. KRINEIA receipts can capture whether belonging preconditions were met before a tool call.

For the full research stack, see [hummbl.io](https://hummbl.io) (forthcoming).
