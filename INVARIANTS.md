# KRINEIA invariants v1.0

**Status**: v1.0 minimum freeze candidate (2026-05-13)

KRINEIA receipts are governance proofs, not observability logs. A receipt chain
is valid only if the system preserving it maintains these four invariants.

## 1. Append-only chain

The receipt log only grows.

- Existing receipts must not be edited in place.
- Existing receipts must not be deleted or compacted.
- Corrections must be appended as new receipts that reference the prior state.
- Forks are allowed only when explicitly recorded as forks; silent rewrites are
  governance failure.

The hash chain makes append-only behavior externally checkable: every receipt
commits to the canonical hash of the previous receipt.

## 2. No reward-path self-reference

Receipt contents must never become part of an agent reward signal, gradient,
policy update, ranking objective, or self-improvement target.

Allowed uses:

- Coordination reads by agents.
- External audit.
- Human or agent review of historical behavior.
- Compliance evidence packaging.

Forbidden uses:

- Training directly on receipt contents.
- Rewarding an agent for producing receipts with desired scores.
- Optimizing future policy behavior against receipt-derived metrics.
- Feeding receipt summaries into an automated self-improvement loop without an
  explicit external review boundary.

This invariant prevents KRINEIA from becoming a target that the governed system
learns to game.

## 3. Minimal operators

The KRINEIA surface is intentionally small:

| Operator | Meaning |
|---|---|
| `append()` | Add a new receipt to the chain. |
| `project()` | Read or transform chain contents without mutation. |
| `cut()` | Produce a bounded excerpt or evidence pack from the chain. |

Any operation outside these three is either an implementation detail of one of
the operators or out of scope for the receipt chain.

Disallowed as first-class chain operations:

- `update()`
- `delete()`
- `rewrite()`
- `summarize_and_replace()`
- `score_and_train()`

Minimal operators keep the chain auditable and reduce the attack surface for
semantic drift.

## 4. External analysis only

KRINEIA is post-mortem infrastructure.

The chain records what happened and supports later analysis, but the chain does
not autonomously steer the system that emits it. Analysis tools may inspect,
query, summarize, or package receipts. They must not mutate historical receipts
or directly update the governed agent's policy from chain contents.

This preserves a hard boundary between:

- **Governance evidence**: immutable receipts and derived evidence packs.
- **Operational control**: the separate systems that decide what agents do next.

## Validity consequence

A chain can pass cryptographic verification while still failing KRINEIA if one
of these invariants is violated. `tools/verify_chain.py` validates receipt
structure and hash linkage; invariant compliance must also be preserved by the
systems that write, store, and consume the chain.
