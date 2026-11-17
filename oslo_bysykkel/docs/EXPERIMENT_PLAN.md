# IKT466 experiments: preregistered draft

This document outlines the two focused investigations before evaluating the
held-out 2026 data. Students should review and adjust choices, then preserve a
version/commit before final testing.

## Research question

How does an MLP compare to a tree-based baseline for forecasting hourly trip-start
counts across Oslo City Bike stations, and how does the amount of training data
affect the two models?

## Inputs and label

- Label: hourly counts of `started_at` in Europe/Oslo timezone.
- Predictors: calendar features known in advance (no observed demand lags,
  no recorded trip duration/end station, no weather).
- The same input features are used by both models to ensure a fair comparison.

## Data split

| Purpose | Period | Notes |
| --- | --- | --- |
| Training | Apr 2–Sep 30, 2024 | Model weights/trees and scaling learned here |
| Validation | Apr 2–Sep 30, 2025 | MLP early stopping and methodological decisions |
| Test | Apr 2–Sep 30, 2026 | Final performance only, not for tuning |

The first calendar day of April is excluded because official CSV boundaries
can be at UTC midnight and March CSVs have not been included. Changing this
requires explicit documentation.

## Investigation 1: two model families

- Random Forest Regressor, 120 trees, minimum leaf size 3.
- MLP with two hidden layers (64, 32), ReLU, MSE loss, Adam optimizer.
- Fixed seed 42, only 2024 data for training, same 2026 test inputs.
- Report MAE and RMSE (primary) and R² (secondary), plus prediction errors
  for the first seven days of each assessment period.
- Interpret any advantage relative to training complexity and data volume;
  do not assume the neural network will win.

## Investigation 2: fraction of labelled training data

- Use 25%, 50%, 100% of 2024 **days** rather than sampling trips randomly.
- Random day selection stratified by month, fixed seed; subsets are nested.
- Validation and test remain identical across runs.
- Measure both model families at each fraction using the same hyperparameters.
- Report the number of training hours per fraction, metrics, and if possible
  the change in performance relative to the full-data setting.
- Note that fewer sampled days can also affect weekday representation;
  a limitation worth discussing.

## Interpretation and limitations

1. Calendar-only features omit storms, major events and local rebalancing.
2. A single training year cannot capture every source of interannual change.
3. We predict **city-wide starts per hour**, not per station.
4. An offline forecast is not equivalent to a production deployment.
5. The dataset counts trips made during the operator's regular opening times;
   zero hours are valid only if monthly data are complete.
6. Repeat runs/seeds if practical to quantify neural-network uncertainty,
   and disclose computing hardware and training time.

## Submission checklist

- [ ] All 18 monthly files checked, source versions recorded in manifest.
- [ ] Splits documented, all preprocessors fit only on training.
- [ ] Validation completed and methodology fixed before opening test results.
- [ ] 2026 metrics and sample errors reported from actual runs.
- [ ] One neural checkpoint, configurations, seeds and reproducibility commands included.
- [ ] Report in MSc thesis format and presentation prepared.
- [ ] Original data and GitHub sources cited; AI tools disclosed.
