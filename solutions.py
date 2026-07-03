"""
SOLUTIONS — don't open until you've attempted the assessment.
Run:  python3 solutions.py   (should score 100/100)
"""
import json
import re

import numpy as np
import pandas as pd

import grader


# ------------------------------------------------------------------ Task 1
def clean_maintenance_logs(df):
    df = df.drop_duplicates().copy()

    def norm_status(s):
        s = re.sub(r"[^a-z]", "", str(s).lower())
        if s in ("op", "operational"):
            return "operational"
        if s.startswith("degrad"):
            return "degraded"
        if "off" in s:
            return "offline"
        return "unknown"

    def to_num(x):
        if pd.isna(x) or str(x).strip() == "":
            return np.nan
        return float(re.sub(r"[^0-9.\-]", "", str(x)))

    out = pd.DataFrame({
        "log_id": df["log_id"],
        "asset_id": df["asset_id"].str.upper(),
        "event_ts": pd.to_datetime(df["event_ts"], format="mixed", dayfirst=False),
        "status": df["status"].map(norm_status),
        "labor_hours": df["labor_hours"].map(to_num),
        "cost_usd": df["cost_usd"].map(to_num),
        "technician": df["technician"].replace("", np.nan),
    })
    # keep latest event per log_id
    out = (out.sort_values("event_ts")
              .groupby("log_id", as_index=False).tail(1)
              .sort_values("log_id").reset_index(drop=True))
    return out


# ------------------------------------------------------------------ Task 2
def flatten_work_orders(payload):
    rows = []
    for item in payload["results"]:
        wo = item["work_order"]
        parts = item.get("parts", [])
        assigned = wo.get("assigned_to")
        rows.append({
            "work_order_id": wo["id"],
            "asset_id": wo["asset"]["id"],
            "facility": wo["asset"]["facility"],
            "priority": wo["priority"],
            "opened_at": pd.to_datetime(wo["opened_at"]),
            "assigned_user": assigned["user"] if assigned else np.nan,
            "parts_count": len(parts),
            "parts_total_cost": round(sum(p["qty"] * p["unit_cost"] for p in parts), 2),
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ Task 3
def facility_summary(clean_logs, assets):
    m = clean_logs.merge(assets[["asset_id", "facility"]], on="asset_id", how="inner")
    g = m.groupby("facility").agg(
        total_events=("log_id", "count"),
        total_cost_usd=("cost_usd", "sum"),
        avg_labor_hours=("labor_hours", "mean"),
        pct_offline=("status", lambda s: (s == "offline").mean()),
    ).reset_index()
    g["total_cost_usd"] = g["total_cost_usd"].round(2)
    g["avg_labor_hours"] = g["avg_labor_hours"].round(3)
    g["pct_offline"] = g["pct_offline"].round(3)
    return g.sort_values("facility").reset_index(drop=True)


# ------------------------------------------------------------------ Task 4
SQL_TASK4 = """
WITH ranked AS (
  SELECT a.facility,
         r.asset_id,
         ROUND(AVG(r.power_kw), 2) AS avg_power_kw,
         RANK() OVER (PARTITION BY a.facility
                      ORDER BY AVG(r.power_kw) DESC) AS facility_rank
  FROM power_readings r
  JOIN assets a ON a.asset_id = r.asset_id
  GROUP BY a.facility, r.asset_id
)
SELECT facility, asset_id, avg_power_kw, facility_rank
FROM ranked
WHERE facility_rank <= 3
ORDER BY facility, facility_rank, asset_id;
"""

# ------------------------------------------------------------------ Task 5
SQL_TASK5 = """
WITH seq AS (
  SELECT asset_id,
         reading_ts,
         LAG(reading_ts) OVER (PARTITION BY asset_id
                               ORDER BY reading_ts) AS prev_ts
  FROM power_readings
)
SELECT asset_id, COUNT(*) AS gap_count
FROM seq
WHERE prev_ts IS NOT NULL
  AND (julianday(reading_ts) - julianday(prev_ts)) * 24 > 3.0
GROUP BY asset_id
HAVING COUNT(*) >= 5
ORDER BY gap_count DESC, asset_id;
"""


# ------------------------------------------------------------------ Task 6
def predict_energy_cost():
    from sklearn.linear_model import LinearRegression
    train = pd.read_csv("data/energy_train.csv")
    test = pd.read_csv("data/energy_test_features.csv")
    feats = ["rated_power_kw", "avg_load_pct", "runtime_hours", "asset_age_years"]
    # kWh interaction term captures the true generating process
    for df in (train, test):
        df["kwh"] = df["rated_power_kw"] * df["avg_load_pct"] * df["runtime_hours"]
    X, y = train[feats + ["kwh"]], train["energy_cost_usd"]
    model = LinearRegression().fit(X, y)
    return model.predict(test[feats + ["kwh"]])


if __name__ == "__main__":
    grader.grade_task1(clean_maintenance_logs)
    grader.grade_task2(flatten_work_orders)
    grader.grade_task3(facility_summary)
    grader.grade_task4(SQL_TASK4)
    grader.grade_task5(SQL_TASK5)
    grader.grade_task6(predict_energy_cost())
    grader.scorecard()
