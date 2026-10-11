# Adaptive Cooling in Metal Fabrication Optimization

A Python research project that generates synthetic metal-cooling process data and performs constrained multi-objective optimization to improve product quality while reducing cooling-system energy consumption.

## Objective

Develop a reproducible Industry 4.0-oriented simulation of an adaptive cooling system for metal fabrication. The system evaluates cooling conditions and optimizes controllable parameters while respecting quality and final-temperature constraints.

## Why this is more than a fixed optimum demo

The optimizer is **not** given a hard-coded answer such as "200 °C and 2 °C/min." Instead, it searches over controllable process variables:

- coolant flow rate,
- fan power,
- cooling duration.

The objective is computed from a synthetic heat-transfer surrogate, a product-quality function, energy consumption, and explicit process constraints. Different measured initial or ambient temperatures can therefore produce different operating recommendations.

## Industry 4.0 relevance

This repository demonstrates several digital-manufacturing concepts:

- synthetic process data for development before plant data is available,
- digital-twin-style surrogate modeling,
- data-driven process evaluation,
- constrained multi-objective optimization,
- adaptive set-point recommendation,
- energy-efficiency and quality trade-off analysis,
- a structure that can later be connected to sensor, IoT, MES, SCADA, or PLC data.

It is a **research and educational simulation**, not production PLC/SCADA control software.

## Model

The synthetic model estimates:

- average cooling rate,
- final workpiece temperature,
- cooling-system energy consumption,
- product quality score,
- defect probability.

Energy includes nonlinear pump demand plus fan electrical energy. Quality penalizes excessive cooling rate, insufficient final cooling, and excessive thermal shock.

These equations are deliberately compact surrogate equations. They are useful for optimization demonstrations but must be calibrated with real thermophysical and plant data before industrial use.

## Project structure

```text
.
├── main.py
├── pyproject.toml
├── requirements.txt
├── LICENSE
├── src/
│   └── adaptive_cooling/
│       ├── __init__.py
│       ├── model.py
│       └── optimize.py
└── tests/
    ├── test_model.py
    └── test_optimization.py
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

The program:

1. generates 5,000 reproducible synthetic observations,
2. saves them to `data/synthetic_cooling_data.csv`,
3. evaluates a fixed-rule baseline,
4. optimizes coolant flow, fan power, and cooling time,
5. reports quality, energy use, final temperature, and defect probability.

## Test

```bash
pytest -q
```

The tests check reproducibility, valid output ranges, basic physical monotonicity, optimizer feasibility, and energy improvement relative to the reference baseline.

## Example result

For the included reference scenario (820 °C initial metal temperature and 25 °C ambient temperature), the validated local run produced approximately:

- baseline quality: 94.97/100,
- baseline energy: 0.8023 kWh,
- optimized quality: 94.29/100,
- optimized energy: 0.2568 kWh,
- energy reduction: about 68%,
- optimized solution feasible under the configured quality and final-temperature constraints.

These values come from the synthetic surrogate model and are not industrial performance claims.

## Example use in an Industry 4.0 architecture

A future industrial implementation could replace the synthetic inputs with real measurements:

```text
Temperature / flow / power sensors
              |
              v
        IoT / OPC UA layer
              |
              v
      Process data platform
              |
              v
     Calibrated cooling model
              |
              v
   Constrained optimizer / MPC
              |
              v
  Validated set-point recommendation
              |
              v
        PLC / operator
```

For a safety-critical or production process, optimization outputs should pass engineering constraints, fail-safe logic, equipment limits, and operator/PLC validation before actuation.

## Limitations

- Data is synthetic.
- The heat-transfer equations are surrogate equations, not a validated finite-element or CFD model.
- Material grade, geometry, phase transformation, residual stress, coolant chemistry, surface condition, and equipment dynamics are simplified or omitted.
- The model must not be treated as a production control system without calibration and validation.

## License

This project is released under the **Jors Academy Non-Commercial Software License 1.0**.

Non-commercial use, study, teaching, and academic research are permitted. Commercial use requires prior written permission from the copyright holder. See `LICENSE` for the complete terms.
