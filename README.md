# Senior Data Engineer Study Guide

This repository is a general study guide for a Senior Data Engineer role, with
notes, practice material, and a mock assessment designed to help you prepare for
interview screens, take-home exercises, and senior-level technical discussions.

The core focus is on the AWS-native data engineering concepts that commonly show
up in senior interviews: S3, Glue, Athena, Lake Formation, streaming, warehousing,
security, orchestration, PySpark, SQL window functions, API ingestion, pipeline
design, and data quality.

## What’s Included
- `senior-data-engineer-study-guide.md` — the main study guide with structured prep notes.
- `study-guide/` — topic-specific reference material organized by subject area.
- `assessment.ipynb` — a 90-minute mock assessment for hands-on practice.
- `grader.py` — local test harness used by the assessment notebook.
- `solutions.py` — reference solutions to review after attempting the assessment.

## Setup
```bash
pip install pandas numpy scikit-learn jupyter
jupyter notebook assessment.ipynb
```

(SQLite ships with Python, so no extra database setup is needed.)

## Study Guide Approach
Use the guide as a broad senior-level review, not just a single exam prep sheet.

- Start with the main guide to get the full map of concepts and likely interview topics.
- Use the topic files under `study-guide/` when you want a deeper refresher on a specific area.
- Treat the assessment notebook as a timed practice run once you are comfortable with the fundamentals.

## Mock Assessment Notes
The assessment is a 90-minute timed practice mirroring the Feenyx/Filtered format:
notebook tasks are graded by test cases, SQL is graded pass/fail, ML is graded on
MAE/RMSE, and written explanations are required.

- `assessment.ipynb` — the timed assessment. Start here when you are ready to practice under time pressure.
- `data/` — messy CSVs, an API JSON payload, and `telemetry.db` (SQLite).
- `solutions.py` — reference solutions. **Do not open until after your attempt.**
  Verify with `python3 solutions.py` (scores 100/100).

## Ground Rules
No AI tools during the 90 minutes — the real platform detects AI use.
Docs are fine. Write every explanation cell; they are scored on the real thing.
