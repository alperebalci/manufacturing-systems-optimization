# Data contracts for real-plant integration

The case modules use small in-code fixtures for reproducible tests. A production integration should map the following fields from governed data sources.

| Case | Typical source | Minimum fields |
|---|---|---|
| 01 Production + maintenance | ERP/MES + CMMS | job id, eligible machine, processing hours, variable cost, risk exposure, PM duration/cost, shift capacity, overtime cost |
| 02 Milk-run | WMS/MES | station, period consumption, line-side inventory, storage capacity, safety stock, tugger capacity/cost |
| 03 AGV | WMS/MES/FMS | task, travel/service time, energy, deadline, priority, vehicle eligibility, SOC/reserve |
| 04 Worker rotation | HR skill matrix + ergonomics | worker qualification, station risk score, shift periods, fatigue/exposure policy |
| 05 Quality MDP | QMS/SPC | process state, inspection policy, transition estimates, inspection/rework/escape costs |
| 06 CNC | machine/process engineering | material, speed/feed/depth bounds, tool-life model, roughness model, power curve, economic coefficients |
| 07 Tooling | MES/toolroom | job, press compatibility, mold family, processing time, due date, setup matrix |
| 08 CONWIP | MES historian | station processing distributions, failure/repair distributions, routing, WIP observations |
| 09 Energy scheduling | MES + energy meter/tariff | processing time, kW, due date/priority, TOU price, planned downtime |
| 10 Cutting stock | ERP/CAD/material store | demand lengths, stock/remnant lengths, quantity available, kerf, material/trim cost |

Production use additionally requires timestamp/version provenance, unit normalization, missing-data rules, change control for cost coefficients, and post-solve reconciliation against the source system.
