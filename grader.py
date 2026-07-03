"""
Feenyx-style mock assessment grader.
Usage from the notebook:

    import grader
    grader.grade_task1(clean_maintenance_logs)
    ...
    grader.scorecard()

Each grader runs test cases against your function, exactly like Feenyx runs
hidden test cases against your modules. Task 6 is scored on RMSE/MAE.
"""
import json
import re
import sqlite3

import numpy as np
import pandas as pd

DATA = "data"
_results = {}


# ----------------------------------------------------------------- helpers
def _record(task, passed, detail, points, earned):
    _results[task] = {"passed": passed, "detail": detail,
                      "points": points, "earned": earned}
    icon = "PASS" if passed else "FAIL"
    print(f"[{icon}] {task}  ({earned}/{points} pts)  {detail}")


def _norm_status(s):
    s = re.sub(r"[^a-z]", "", str(s).lower())
    if s in ("op", "operational"):
        return "operational"
    if s.startswith("degrad"):
        return "degraded"
    if "off" in s:
        return "offline"
    return "unknown"


def _to_num(x):
    if pd.isna(x) or str(x).strip() == "":
        return np.nan
    return float(re.sub(r"[^0-9.\-]", "", str(x)))


# ----------------------------------------------------------------- reference solutions
def _ref_task1():
    df = pd.read_csv(f"{DATA}/maintenance_logs_raw.csv", dtype=str)
    df = df.drop_duplicates()
    out = pd.DataFrame({
        "log_id": df["log_id"],
        "asset_id": df["asset_id"].str.upper(),
        "event_ts": pd.to_datetime(df["event_ts"], format="mixed", dayfirst=False),
        "status": df["status"].map(_norm_status),
        "labor_hours": df["labor_hours"].map(_to_num),
        "cost_usd": df["cost_usd"].map(_to_num),
        "technician": df["technician"].fillna("").replace("", np.nan),
    })
    out = (out.sort_values("event_ts")
              .groupby("log_id", as_index=False).tail(1)
              .sort_values("log_id").reset_index(drop=True))
    return out


def _ref_task2():
    with open(f"{DATA}/work_orders_api.json") as f:
        payload = json.load(f)
    rows = []
    for item in payload["results"]:
        wo = item["work_order"]
        parts = item.get("parts", [])
        rows.append({
            "work_order_id": wo["id"],
            "asset_id": wo["asset"]["id"],
            "facility": wo["asset"]["facility"],
            "priority": wo["priority"],
            "opened_at": pd.to_datetime(wo["opened_at"]),
            "assigned_user": (wo.get("assigned_to") or {}).get("user", np.nan),
            "parts_count": len(parts),
            "parts_total_cost": round(sum(p["qty"] * p["unit_cost"] for p in parts), 2),
        })
    return pd.DataFrame(rows).sort_values("work_order_id").reset_index(drop=True)


def _ref_task3():
    logs = _ref_task1()
    assets = pd.read_csv(f"{DATA}/asset_reference.csv")
    m = logs.merge(assets[["asset_id", "facility"]], on="asset_id", how="inner")
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


_REF_SQL4 = """
WITH ranked AS (
  SELECT a.facility, r.asset_id,
         ROUND(AVG(r.power_kw), 2) AS avg_power_kw,
         RANK() OVER (PARTITION BY a.facility
                      ORDER BY AVG(r.power_kw) DESC) AS rnk
  FROM power_readings r JOIN assets a USING (asset_id)
  GROUP BY a.facility, r.asset_id
)
SELECT facility, asset_id, avg_power_kw, rnk AS facility_rank
FROM ranked WHERE rnk <= 3
ORDER BY facility, facility_rank, asset_id;
"""

_REF_SQL5 = """
WITH seq AS (
  SELECT asset_id, reading_ts,
         LAG(reading_ts) OVER (PARTITION BY asset_id ORDER BY reading_ts) AS prev_ts
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


def _run_sql(sql):
    conn = sqlite3.connect(f"{DATA}/telemetry.db")
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


# ----------------------------------------------------------------- comparison
def _compare_df(got, exp, float_cols=(), task="", points=0, key_cols=None):
    try:
        if not isinstance(got, pd.DataFrame):
            _record(task, False, f"expected a DataFrame, got {type(got).__name__}", points, 0)
            return
        missing = set(exp.columns) - set(got.columns)
        if missing:
            _record(task, False, f"missing columns: {sorted(missing)}", points, 0)
            return
        got = got[list(exp.columns)].copy()
        if key_cols:
            got = got.sort_values(list(key_cols)).reset_index(drop=True)
            exp = exp.sort_values(list(key_cols)).reset_index(drop=True)
        if len(got) != len(exp):
            _record(task, False, f"row count {len(got)} != expected {len(exp)}", points, 0)
            return
        for c in exp.columns:
            if c in float_cols:
                g = pd.to_numeric(got[c], errors="coerce")
                e = pd.to_numeric(exp[c], errors="coerce")
                ok = np.isclose(g.fillna(-9e9), e.fillna(-9e9), atol=0.02).all()
            elif pd.api.types.is_datetime64_any_dtype(exp[c]):
                ok = pd.to_datetime(got[c]).reset_index(drop=True).equals(
                    exp[c].reset_index(drop=True))
            else:
                ok = got[c].astype(str).fillna("nan").reset_index(drop=True).equals(
                    exp[c].astype(str).fillna("nan").reset_index(drop=True))
            if not ok:
                bad = c
                _record(task, False, f"column '{bad}' does not match expected output", points, 0)
                return
        _record(task, True, "all test cases passed", points, points)
    except Exception as e:  # noqa: BLE001
        _record(task, False, f"error while grading: {e!r}", points, 0)


# ----------------------------------------------------------------- public graders
def grade_task1(func):
    """func(raw_df) -> cleaned DataFrame"""
    raw = pd.read_csv(f"{DATA}/maintenance_logs_raw.csv", dtype=str)
    try:
        got = func(raw.copy())
    except Exception as e:  # noqa: BLE001
        _record("Task 1 - Clean maintenance logs", False, f"function raised {e!r}", 25, 0)
        return
    exp = _ref_task1()
    _compare_df(got, exp,
                float_cols=("labor_hours", "cost_usd"),
                task="Task 1 - Clean maintenance logs", points=25,
                key_cols=("log_id",))


def grade_task2(func):
    """func(payload_dict) -> flattened DataFrame"""
    with open(f"{DATA}/work_orders_api.json") as f:
        payload = json.load(f)
    try:
        got = func(payload)
    except Exception as e:  # noqa: BLE001
        _record("Task 2 - Flatten API payload", False, f"function raised {e!r}", 15, 0)
        return
    exp = _ref_task2()
    _compare_df(got, exp, float_cols=("parts_total_cost",),
                task="Task 2 - Flatten API payload", points=15,
                key_cols=("work_order_id",))


def grade_task3(func):
    """func(clean_logs_df, assets_df) -> facility summary DataFrame"""
    assets = pd.read_csv(f"{DATA}/asset_reference.csv")
    try:
        got = func(_ref_task1(), assets)
    except Exception as e:  # noqa: BLE001
        _record("Task 3 - Facility summary", False, f"function raised {e!r}", 15, 0)
        return
    exp = _ref_task3()
    _compare_df(got, exp,
                float_cols=("total_cost_usd", "avg_labor_hours", "pct_offline"),
                task="Task 3 - Facility summary", points=15,
                key_cols=("facility",))


def grade_task4(sql):
    """sql: string. Top-3 assets by avg power per facility."""
    try:
        got = _run_sql(sql)
    except Exception as e:  # noqa: BLE001
        _record("Task 4 - SQL window ranking", False, f"query failed: {e!r}", 15, 0)
        return
    exp = _run_sql(_REF_SQL4)
    got.columns = [c.lower() for c in got.columns]
    _compare_df(got, exp, float_cols=("avg_power_kw",),
                task="Task 4 - SQL window ranking", points=15,
                key_cols=("facility", "facility_rank", "asset_id"))


def grade_task5(sql):
    """sql: string. Telemetry gap detection with LAG."""
    try:
        got = _run_sql(sql)
    except Exception as e:  # noqa: BLE001
        _record("Task 5 - SQL gap detection", False, f"query failed: {e!r}", 15, 0)
        return
    exp = _run_sql(_REF_SQL5)
    got.columns = [c.lower() for c in got.columns]
    _compare_df(got, exp, task="Task 5 - SQL gap detection", points=15,
                key_cols=("asset_id",))


def grade_task6(predictions):
    """predictions: array-like of predicted energy_cost_usd for energy_test_features.csv"""
    y_true = pd.read_csv(f"{DATA}/.energy_test_labels_hidden.csv")["energy_cost_usd"].values
    try:
        y_pred = np.asarray(predictions, dtype=float).ravel()
    except Exception as e:  # noqa: BLE001
        _record("Task 6 - Cost prediction", False, f"could not read predictions: {e!r}", 15, 0)
        return
    if y_pred.shape[0] != y_true.shape[0]:
        _record("Task 6 - Cost prediction", False,
                f"expected {y_true.shape[0]} predictions, got {y_pred.shape[0]}", 15, 0)
        return
    mae = float(np.mean(np.abs(y_pred - y_true)))
    rmse = float(np.sqrt(np.mean((y_pred - y_true) ** 2)))
    if rmse <= 12.0:
        earned, passed = 15, True
    elif rmse <= 25.0:
        earned, passed = 8, False
    else:
        earned, passed = 0, False
    _record("Task 6 - Cost prediction", passed,
            f"MAE={mae:.2f}, RMSE={rmse:.2f} (full credit: RMSE <= 12.00)", 15, earned)


def scorecard():
    total = sum(r["points"] for r in _results.values())
    earned = sum(r["earned"] for r in _results.values())
    print("\n" + "=" * 58)
    print(f"{'TASK':<38}{'SCORE':>10}")
    print("-" * 58)
    for t, r in _results.items():
        print(f"{t:<38}{r['earned']:>5}/{r['points']}")
    print("-" * 58)
    pct = 100 * earned / total if total else 0
    print(f"{'TOTAL':<38}{earned:>5}/{total}   ({pct:.0f}%)")
    print("=" * 58)
    if pct >= 80:
        print("Result: STRONG PASS - typical advance threshold cleared.")
    elif pct >= 60:
        print("Result: BORDERLINE - review failed tasks and retry.")
    else:
        print("Result: BELOW BAR - drill the failed areas before the real thing.")
