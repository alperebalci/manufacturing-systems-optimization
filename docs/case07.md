# Case 07 — Tooling / mold-aware press scheduling

Decision: assign jobs to compatible presses and determine sequence.

Processing times are press-dependent. Jobs carry mold family, due date and tardiness weight. Sequence-dependent mold changeovers use an asymmetric setup matrix, including a small same-family setup. The bundled instance is small enough for exact assignment-and-permutation enumeration.

Baseline: EDD jobs assigned to the currently lighter compatible press.

Audit: all jobs scheduled once and press compatibility respected.

KPIs: weighted tardiness, makespan and setup hours.
