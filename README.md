# HUMMBL Verum

The append-only sovereignty layer of the [HUMMBL](https://hummbl.io) stack.

> **Verum** (Latin: "true") — cryptographically chained, append-only governance receipts. Proves that a decision happened, by whom, in what state, with what deviation from setpoint. Receipts are post-mortem-only audit artifacts: agents may **read** the chain for coordination, but chain contents NEVER feed back into any agent's reward, gradient, or policy-update path.

## What's in this repo

| File | Status | Purpose |
|---|---|---|
| [`RECEIPT_SCHEMA.md`](RECEIPT_SCHEMA.md) | v0.1 | Canonical schema for receipts emitted by Verum and consumed by `verum-mcp` |
| `LICENSE` | Apache-2.0 | License (full text) |
| `README.md` | this file | What you're reading |

Forthcoming (v0.1 → v1.0):

- `INVARIANTS.md` — the four governing invariants (append-only, no reward-path self-reference, minimal operators, external analysis only)
- `VALIDATOR.md` — algorithm + reference implementation for independent chain verification
- `MCP_INTERFACE.md` — `verum-mcp` tool surface (Model Context Protocol)
- `tools/verify_chain.py` — standalone validator, stdlib-only
- `daemon/` — reference daemon implementation (currently at `C:/Users/Owner/overnight/`, will move once stable)

## Why this exists

Most "AI governance" tooling treats audit logs as observability — a side channel that gets flushed, summarized, or eventually overwritten. Verum makes the opposite bet: **the audit log is the governance**. If a tool call wasn't recorded with a verifiable hash chain back to a known-good genesis, no governance happened. Period.

The four invariants make this operational:

1. **Append-only** — the log only grows. No deletes, no mutations, ever.
2. **No reward-path self-reference** — log contents never enter any agent's reward, gradient, or training signal. (Reading for coordination is allowed; learning from the log is not.)
3. **Minimal operators** — exactly three: `append()`, `project()`, `cut()`. Anything more is leakage.
4. **External analysis only** — the log is post-mortem. External tools inspect; the system itself doesn't.

These are NOT software-engineering conventions; they are the load-bearing properties that distinguish a governance proof from a self-referential optimization target.

## Status

**v0.1 — DRAFT.** Schema captures the format emitted by the v0.1 reference daemon. v1.0 will be frozen for the May 15 2026 LOI gate.

This repo is the **canonical** Verum spec. The reference daemon, validator, and MCP interface are tracked here (or will move here) for SPDX-resolvable provenance.

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).

Receipt format and validator algorithm are intended to be implementable freely; HUMMBL Verum the trademark / brand is not granted by this license.

## Related work

- **VERUM (theory)** — the governing invariants in `~/.claude/rules/hummbl-primitives.md` (Layer 2 of the HUMMBL stack)
- **Base120 (mental models)** — Layer 1 of the HUMMBL stack; receipts capture which Base120 operator was selected per decision
- **BKI (belonging)** — Layer 3 of the HUMMBL stack; receipts verify that belonging preconditions were met before content delivery

For the full HUMMBL stack picture, see [hummbl.io](https://hummbl.io) (forthcoming) and the canonical primitives doc.
