# KRINEIA invariants v1.0

**Status**: v1.0-rc2 (2026-05-15)

KRINEIA receipts are governance proofs, not observability logs. A receipt chain
is valid only if the system preserving it maintains these five invariants.

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

## 5. Trust-root separation

The receipt chain must be written by a system structurally independent of the
agent it observes. The observed agent must have no write authority over the
chain -- neither direct (writing receipts) nor indirect (controlling the
receipt-generation process).

### Allowed observer architectures

- Separate process under shared operating control (v0.1 deployment-asserted).
- Separate machine.
- Asymmetric cryptography proving independence from the observed system --
  KRINEIA holds the private key, agent holds nothing (v0.2 candidate).

### Forbidden

- The observed agent generates its own receipts.
- The observed agent holds the signing keys for the chain.
- The receipt-generation logic is part of the agent's policy network.

### Why this is distinct from invariant 2

Invariant 2 prevents the chain's CONTENTS from entering the agent's reward path.
Invariant 5 prevents the chain's GENERATION from doing so.

If the agent generates its own receipts AND those receipts are a precondition
for operational outputs (egress, action authorization, downstream consumption),
then "produce a valid receipt" becomes a sub-goal of "act." The agent will
optimize for valid-seal-as-such even if it never sees the seal contents in
training. Invariant 5 closes that gap.

### Validity consequence

A v0.1 deployment can satisfy invariant 5 by process boundary alone (separate
observer process, no agent write path). A v0.2+ deployment can additionally
satisfy it cryptographically (per-receipt asymmetric signature with external
key custody). The cryptographic path moves the trust root from
"deployment-asserted" to "cryptographically-asserted" and survives compromise
of the observed agent.

## Validity consequence

A chain can pass cryptographic verification while still failing KRINEIA if one
of these invariants is violated. `tools/verify_chain.py` validates receipt
structure and hash linkage; invariant compliance must also be preserved by the
systems that write, store, and consume the chain.
