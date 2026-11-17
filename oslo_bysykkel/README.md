# IKT466 — Oslo Bysykkel: Hourly Rental Demand Forecasting

**Status:** Starter code, not yet a finished empirical project. No Oslo experiment results
are bundled. Add the actual Oslo trip CSVs, inspect them, then run the experiments.

## Research question

How does a PyTorch MLP compare with a Random Forest when predicting the number of
Oslo City Bike trips starting in each hour, and how does training-data quantity
change their predictive performance?

- **Target:** `demand` = number of trip starts per hour **across all Oslo stations**.
- **Predictors:** calendar features available before the hour (hour, weekday, month,
  cyclic encodings, summer, weekend and a rush-hour indicator).
- **Not included:** weather or lagged demand; do not claim these were used.
- **Models:** RandomForestRegressor from scikit-learn; PyTorch MLP with hidden layers 64/32.
- **Experiment 1:** compare RF and MLP at 100% of 2024 training data.
- **Experiment 2:** compare 25%, 50% and 100% of 2024 training days, sampled within
  month with fixed seed; validation and test are never resampled.
- **Evaluation:** MAE, RMSE, R², plots, saved hourly predictions and training curves.

## Data source & licence

**Oslo Bysykkel historical trips:**
https://oslobysykkel.no/en/open-data/historical

The official open data are distributed under the **Norwegian Licence for Open Government
Data (NLOD) 2.0**: https://data.norge.no/nlod/no/2.0 . Attribute Oslo Bysykkel in the report.

Each file contains anonymised trips, with an offset-aware `started_at` timestamp.
Individual trip records are transformed to hourly trip-start counts. Only `started_at`
is used; `ended_at`, trip duration, station destination etc. cannot leak into features.

**Folder naming convention** (six months April–September per year, 18 files total):

```text
data/raw/
  2024/04.csv  2024/05.csv ... 2024/09.csv
  2025/04.csv  2025/05.csv ... 2025/09.csv
  2026/04.csv  2026/05.csv ... 2026/09.csv
```

The source files may instead be imported with `python import_csv.py --year 2024
--month 4 --file "path/to/downloaded.csv"`.

**Why April–September?** To compare the same six months over three years and
avoid extrapolating across the off-season. Conclusions do **not** apply to winter.
The script refuses missing files: missing months must never be mistaken for zero rentals.

**UTC/local-time subtlety:** Oslo publishes data aligned to UTC; Oslo calendar days
start earlier than the corresponding UTC day. To avoid incomplete coverage without
March CSVs, `drop_first_day_of_season=true` excludes **April 1** from all three
partitions. Other hours are indexed in `Europe/Oslo`, preserving local calendar features.
Empty hourly bins in months with a supplied file are treated as zero trips. Check
source completeness and operating hours before interpreting these bins. If any month
is only partially published, replace it with the complete file before preparation.

## Setup (Python 3.10 or later)

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

`torch` may need installation using the official PyTorch CPU or GPU wheel as
appropriate for your platform: https://pytorch.org/get-started/locally/

## Run from the PROJECT ROOT

```bash
# 1. Add all 18 source CSV files (or import them one by one).
python import_csv.py --year 2024 --month 4 --file "C:/Downloads/04.csv"

# 2. Build a single hourly table and document exactly which source files were used.
python prepare_data.py

# 3. Experiment on validation year (2025) first.
python run_experiments.py --phase validation

# 4. AFTER fixing the methodology and hyperparameters, run held-out 2026 evaluation ONCE.
python run_experiments.py --phase test

# 5. Optional: predict the expected trips starting in a given local Oslo hour.
python predict.py --hour "2026-09-15 08:00"
```

If the files have not been provided, `prepare_data.py` prints an explicit list of
missing CSVs. The project is deliberately not using fake/example data as findings.

## Expected results (only after actual runs)

```text
data/processed/hourly_demand.csv
data/processed/source_manifest.csv        # file sizes, row counts, SHA-256 digests
data/processed/split_definition.json
outputs/validation/metrics.csv
outputs/test/metrics.csv
outputs/test/predictions_randomforest_100pct.csv
outputs/test/predictions_mlp_100pct.csv
outputs/test/random_forest.joblib
outputs/test/mlp_checkpoint.pt
outputs/test/mlp_learning_curve.png
outputs/test/plot_randomforest.png
outputs/test/plot_mlp.png
```

A run records versions, settings and seed in `run_metadata.json`. Saved raw
predictions permit error analysis by hour, weekend and season. Interpret results
from **Oslo only** and never copy the original GitHub repository's UCI scores.

## Explanation of validation / leakage rules

- Train: April 2–September 30 **2024**.
- Validation: April 2–September 30 **2025**. Used for MLP early stopping and method design.
- Test: April 2–September 30 **2026**. No tuning or model selection on this set.
- Only training data fit the MLP input/target scalers.
- Each training fraction samples whole days within each month with a fixed seed.
- Same target and input features for both models; no future trip counts as features.
- For final report, discuss that a calendar-only model omits weather, events and
  recent-demand lags, and that using a single training year limits generalisation.
- To assess operational usability, more comparisons, day-type stratification and
  independent validation may be warranted, if time permits.

## Project map

```text
config.json                  # All choices and fixed hyperparameters
import_csv.py                # Put a downloaded month in the right folder
prepare_data.py              # Read trip CSVs and aggregate hours
run_experiments.py           # RF/MLP, two comparisons, metrics, figures
predict.py                   # Optional inference from trusted RF model
src/data.py                  # Offset-aware dates, input validation, splits
src/features.py              # Calendar-only predictors
src/models.py                # RF + MLP training and checkpoint persistence
src/evaluate.py              # Metrics, figures, prediction CSVs
tests/test_pipeline.py       # Automated checks without actual results
START_HERE_AR.md             # Step-by-step instructions in Arabic
SOURCE_ATTRIBUTION.md       # Credit and reproducibility details
```

## Academic provenance & GitHub reference

The following public repository informed this starter's **workflow and layout**:

- Alvaro Gonzalez, *Bike-Sharing Hourly Demand Forecasting*:
  https://github.com/alvarogrojas/bike-sharing-demand-forecasting
  (original project uses **UCI Washington D.C.** data, 2011–2012).

Its README describes chronological validation, cyclic calendar features and
reproducible evaluation. **This starter is a freshly written adaptation,
not a fork and not a verbatim copy of the upstream files**: direct cloning from
this environment was unavailable. See `SOURCE_ATTRIBUTION.md` for details.
The original project uses the MIT license (Copyright 2026 Alvaro Gonzalez);
if actual upstream source is imported later, keep its copyright/license notice.

For IKT466, cite all external code and datasets. All published findings and
figures must come from your own experiments. An AI-use statement is also
required by the project overview.

## Not included (yet)

The dataset itself, real evaluation results, narrative MSc-thesis report and
presentation are not yet complete. These should follow after the real CSVs
and your own experiment executions are available.
