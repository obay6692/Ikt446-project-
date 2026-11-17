# Testing notes — not a research result

This starter was checked in the working environment before packaging.

1. Automated unit tests passed (`python -m unittest discover -s tests -v`).
2. The previously uploaded file `10.csv` (October 2026) was read successfully
   using `src.data.read_month` as a compatibility check: **107,223 trip rows**,
   **582 nonempty UTC hourly bins**, and **0 invalid timestamps**.
   This October file is **NOT included** in the project archive or Apr-Sep study.
3. The full prepare → validation → test → prediction workflow was executed
   on **synthetic data generated into a temporary testing directory**.
   This verified that the code path works but produced **no valid Oslo research
   results**. Those synthetic CSVs, metrics and checkpoints are NOT included.
4. Actual modelling, results, interpretation and report remain to be performed
   using the official real files for April–September 2024, 2025 and 2026.

No accuracy claims can be made at this stage.
