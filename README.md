# Mock Feenyx Data Engineering Assessment

90-minute timed practice mirroring the Feenyx/Filtered format: notebook tasks graded
by test cases, SQL graded pass/fail, ML graded on MAE/RMSE, written explanations required.

## Setup
```bash
pip install pandas numpy scikit-learn jupyter
jupyter notebook assessment.ipynb
```
(SQLite ships with Python — no DB setup needed.)

## Files
- `assessment.ipynb` — the timed assessment. Start here.
- `grader.py` — local test harness (called from the notebook).
- `data/` — messy CSVs, an API JSON payload, and `telemetry.db` (SQLite).
- `solutions.py` — reference solutions. **Do not open until after your attempt.**
  Verify with `python3 solutions.py` (scores 100/100).

## Ground rules
No AI tools during the 90 minutes — the real platform detects AI use.
Docs are fine. Write every explanation cell; they are scored on the real thing.
