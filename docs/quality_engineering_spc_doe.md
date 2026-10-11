# Statistical Quality Engineering: DOE, SPC, and Capability

Modern IE/OR programs should not treat quality as only another penalty term inside an optimizer. Before optimizing a manufacturing process, engineers need to know whether the process is stable, which controllable factors matter, and whether the resulting process is capable of meeting engineering specifications.

This cross-cutting lab adds three classical quality-engineering techniques to the manufacturing portfolio while keeping them connected to modern computational workflows.

## 1. Two-level factorial design of experiments

The full_factorial function creates a reproducible 2^k design with both coded (-1/+1) and physical factor levels.

The factorial_effects function estimates main and interaction effects on the standard high-minus-low scale. This gives a transparent first screen for questions such as:

- Which controllable process factors materially change the response?
- Are interactions large enough that one-factor-at-a-time reasoning is misleading?
- Which factors should enter a later response-surface, Bayesian-optimization, or constrained-optimization model?

The recommend_factorial_setting function selects the best observed factorial setting using replicated mean response. It is deliberately simple: DOE is being used to learn the process before a more elaborate optimizer is justified.

## 2. Statistical process control

The individuals_control_chart function implements an Individuals chart with the average-moving-range estimate of process sigma:

    sigma_hat = MR_bar / 1.128

The default control limits are:

    center +/- 3 * sigma_hat

The baseline sample determines the center and limits; later observations are then checked against those limits.

A control limit is not a specification limit. SPC asks whether the process is statistically stable. Engineering specifications ask whether output is acceptable.

## 3. Process capability

The process_capability function reports:

- Cp: potential capability given process spread;
- Cpk: realized capability after accounting for off-centering;
- upper and lower one-sided capability indices.

Capability metrics should only be interpreted after process stability and measurement-system adequacy have been considered.

## Suggested manufacturing workflow

    measurement-system / data check
                |
                v
    baseline SPC stability
                |
                v
    factorial DOE
                |
                v
    important factors + interactions
                |
                v
    optimization / response-surface / Bayesian search
                |
                v
    confirmation run
                |
                v
    SPC monitoring + capability

This creates a stronger bridge between classical industrial engineering and modern optimization than optimizing a noisy or unstable process blindly.

## Scope and limitations

- The DOE helper covers balanced two-level full factorials; fractional factorials, blocking, randomization restrictions, center points, and response-surface designs are separate extensions.
- The Individuals chart assumes a meaningful stable baseline and uses the standard moving-range estimator for consecutive individual observations.
- Cp/Cpk alone are not evidence of control, causality, or customer impact.
- Real deployments require measurement-system analysis, domain-appropriate sampling, engineering specifications, and a reaction plan for out-of-control signals.

The module is intended as a compact curriculum-quality lab that complements the repository's optimization cases.
