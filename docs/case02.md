# Case 02 — Milk-run line feeding

Decision: how much material to deliver to each station each period and how many tugger trips to release.

Inventory balance includes initial line-side stock, planned delivery, emergency supply and consumption. Storage capacity and safety-stock floors are explicit. Planned delivery volume is bounded by integer trips × vehicle capacity.

Baseline: greedy refill-to-target policy using the same storage and trip limits.

Audit: period-by-period material balance, storage limits, safety stock, vehicle capacity and trip limits.

KPIs: total logistics cost, emergency units, trip count. sensitivity() changes tugger capacity.
