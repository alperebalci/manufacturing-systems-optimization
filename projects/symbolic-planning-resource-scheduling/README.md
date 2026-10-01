# Symbolic Planning and Resource Scheduling

Implemented bounded research baseline, v0.1, 2026-10-01.

A time-indexed MILP jointly selects symbolic actions and schedules them under renewable resource calendars. Preconditions must be established by completed actions before a successor starts. Alternative actions may produce the same fact, but this restricted model produces each noninitial fact at most once. Positive action durations prevent cyclic preconditions from bootstrapping themselves. The objective is lexicographic makespan then nonnegative action cost using a valid instance-derived weight.

Replanning can preserve committed action starts while enforcing an earliest start for new actions. An independent schedule auditor checks facts, goals, precedence and resource use; exhaustive enumeration verifies tiny instances.

## Run

```bash
python -m pip install -r requirements.txt
python -m unittest checks -v
python study.py --output local-results.json
```

Core API: Action, plan(actions,initial,goals,capacities,H), audit, exhaustive. Seven local checks passed.

The executed fixture chooses buy_A and cut_B in parallel, then assembly: makespan 4, cost 7. A vendor outage changes the action plan to sequential cut_A/cut_B then assembly: makespan 5, cost 3. Replanning preserves an already committed cut_A start. These are small synthetic verification results, not industrial savings.

## Boundaries

Finite horizon, integer action start times, positive integer durations and monotone add-only facts. No delete effects, negative preconditions, general PDDL parser, geometric streams or PDDLStream reproduction. Each action executes at most once. Optimality is for this bounded model; physical execution uncertainty is outside scope. This is an adjacent module and does not modify existing manufacturing studies.

Primary research context: https://ojs.aaai.org/index.php/ICAPS/article/view/6739

Independent implementation. Existing repository license applies. Source fingerprints and environment are in VALIDATION.json. The explicit checks.py runner leaves root pytest discovery unchanged.
