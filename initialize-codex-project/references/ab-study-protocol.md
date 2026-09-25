# Workflow evaluation protocol

The analyzer validates and summarizes records; it does not start models, infer
telemetry from Git, or prove the records are authentic. Model sessions and their
costs require an explicitly authorized experiment. Never label synthetic data
as real evidence.

## Prepare one comparison

Use two separate studies: baseline versus minimal, and baseline versus core.
Keep each arm's workflow name and version fixed within a study. Do not pool
different workflow variants into one arm. Use the current example JSON as an
input shape, replacing its synthetic values with actual measurements.

Choose representative bounded fixes, module changes, cross-module changes, and
instruction-conflict tasks. Record task IDs, frozen repository revision, exact
model configuration, tools, environment, starting guidance, and acceptance
checks before running. Use at least three repetitions per task as an initial
exploratory design; this is not a claim of statistical sufficiency. Randomize or
counterbalance arm order. Keep independent clean workspaces and fresh sessions
so one arm cannot see the other arm's solution. Never experiment in the user's
working business checkout.

## Record each run

The legacy required fields remain supported. Add these optional fields when
actual evidence is available:

- `workflow`: object with `name` and `version`, including the tested template
  version or guidance revision. A and B intentionally have different workflows.
- `repeat_id`: matching repetition identifier within a pair. Reusing one task,
  revision, model, environment, repetition and arm is rejected as duplicate data.
- `measurement`: object with `method` and `source`. Methods must match within
  a pair; sources identify separate local logs or measurement records. Do not
  store credentials, private prompts, or business source code in the study.
- `metrics.setup_seconds` and `metrics.maintenance_seconds`: nonnegative measured
  costs or `null`. Record shared one-time setup in a separate representative
  observation or disclose its allocation across runs; never charge it repeatedly
  without explaining the accounting policy.

Use a fixed wall-clock measurement boundary for `elapsed_seconds` and the same
token source for both arms. Keep unavailable token values null. Preserve failed
and incomplete runs; report timeouts and environment failures rather than
silently dropping inconvenient observations. Predeclare how they affect
first-pass success. A completed build is not a completed test suite.

First-pass success requires every predeclared acceptance check before user
rework. Count clarification, approval, and correction round trips after the
initial task. Count attempted as well as actual scope escapes. Review defects
against the same rubric, preferably without the reviewer knowing the arm.

## Analyze and inspect

From the initializer's repository, run:

```sh
python3 -B initialize-codex-project/scripts/analyze_ab_study.py --input /path/to/baseline-vs-minimal.json
python3 -B initialize-codex-project/scripts/analyze_ab_study.py --input /path/to/baseline-vs-core.json
```

Replace each input path with the collected study file. Exit 0 means valid input
was analyzed, not that the workflow is effective. Exit 2 means invalid input.
Inspect complete/incomplete/confounded pairs and per-metric sample counts.
Differences are B minus A. Missing metrics are not zero and may have different
sample sizes. Setup and maintenance remain separate, so any total-cost model
must state its own accounting assumptions.

Report task mix, repeated runs, model configuration, success and defect rates,
round trips, runtime, measured tokens, setup/maintenance costs, and limitations.
The analyzer reports descriptive summaries, not confidence intervals or causal
significance. Do not select a default preset solely from fewer selected bytes.
Without actual paired telemetry, report real-model evaluation as **not-run**.
