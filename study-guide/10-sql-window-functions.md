# 10 — SQL & Window Functions

Prereq: basic SQL (`SELECT`, `WHERE`, `GROUP BY`, `JOIN`). This is a **coding** chapter. **Window functions are the senior-level filter** — they separate junior from senior in almost every data assessment. Master this chapter.

---

## The one idea behind window functions

A normal `GROUP BY` **collapses** many rows into one summary row. A **window function computes across a set of related rows but keeps every row.** You get the aggregate/ranking *alongside* the original detail — no collapsing.

The syntax is always:

```sql
FUNCTION(...) OVER (
  PARTITION BY <group columns>      -- optional: reset the calc per group
  ORDER BY <sort columns>           -- optional: order within the group
  ROWS BETWEEN ... AND ...          -- optional: the moving frame
)
```

- **`PARTITION BY`** — split rows into groups; the function restarts per group. (Like `GROUP BY` but without collapsing.)
- **`ORDER BY`** — order rows within each group (needed for rankings, running totals, LAG/LEAD).
- **The frame** (`ROWS BETWEEN ...`) — which surrounding rows to include (for moving averages).

---

## Pattern 1 — Deduplicate to the latest record per key

The single most common assessment problem. "Keep only the newest row per customer."

```sql
SELECT * FROM (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY customer_id
           ORDER BY updated_at DESC
         ) AS rn
  FROM customers_raw
) WHERE rn = 1;
```

Number rows within each customer, newest first, keep #1. **Note the subquery** — you can't put a window function directly in `WHERE` (and Athena has no `QUALIFY`, so the subquery is mandatory there).

### The three ranking functions (know the difference cold)

Given values 100, 90, 90, 80:

| Function | Result | Behavior on ties |
|---|---|---|
| `ROW_NUMBER()` | 1, 2, 3, 4 | Always unique — arbitrary tie-break |
| `RANK()` | 1, 2, 2, 4 | Ties share rank, then **skips** |
| `DENSE_RANK()` | 1, 2, 2, 3 | Ties share rank, **no gaps** |

- Deduping to one row → **`ROW_NUMBER`**.
- "Top 3 including ties" → **`DENSE_RANK`** (or `RANK`) with `<= 3`.

---

## Pattern 2 — Running totals & moving averages

```sql
SELECT order_date,
       SUM(amount) OVER (ORDER BY order_date) AS running_total,
       AVG(amount) OVER (
         ORDER BY order_date
         ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ) AS moving_avg_7d
FROM daily_sales;
```

- `SUM(...) OVER (ORDER BY order_date)` — a **cumulative** sum (each row adds to all prior).
- The **frame** `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` = this row plus the previous 6 = a **7-row moving window.**

---

## Pattern 3 — LAG / LEAD (compare to the previous/next row)

`LAG` looks **backward**, `LEAD` looks **forward**. Used for deltas and sessionization.

```sql
-- Sessionization: start a new session after 30 min of inactivity
SELECT user_id, event_ts,
       CASE WHEN event_ts - LAG(event_ts) OVER (
              PARTITION BY user_id ORDER BY event_ts
            ) > INTERVAL '30' MINUTE
            THEN 1 ELSE 0 END AS new_session_flag
FROM events;
```

`LAG(event_ts)` gives the previous event's time for that user; if the gap exceeds 30 minutes, it's a new session. This "gaps and islands" style problem is a classic senior question.

---

## Pattern 4 — Top-N per group

"Top 3 products by revenue in each region":

```sql
SELECT * FROM (
  SELECT region, product, revenue,
         DENSE_RANK() OVER (
           PARTITION BY region ORDER BY revenue DESC
         ) AS rk
  FROM sales
) WHERE rk <= 3;
```

`PARTITION BY region` restarts the ranking per region; keep ranks `<= 3`.

---

## Other SQL you must review

- **CTEs (`WITH`)** — name a subquery to make complex queries readable. Chain several `WITH a AS (...), b AS (...)`.
- **Anti-join (find what's missing):**
  ```sql
  SELECT o.* FROM orders o
  LEFT JOIN shipments s ON o.id = s.order_id
  WHERE s.order_id IS NULL;      -- orders with no shipment
  ```
  Equivalent with `NOT EXISTS`. (In Spark: `left_anti` join.)
- **`UNNEST`** — flatten an array column into rows (Athena/Trino). Spark's `explode`.
- **`date_trunc('month', ts)`** — bucket timestamps to day/month/year.
- **`try_cast(x AS int)`** — cast dirty data without erroring (returns NULL on failure). Essential for messy input.
- **`COALESCE(a, b, c)`** — first non-null value; handy for defaults/null handling.
- **`QUALIFY`** — filters on window functions directly in some engines (Snowflake, BigQuery, Databricks) — but **Athena/Trino does NOT support it**, so wrap in a subquery there.

---

## Key facts to memorize

- Window function = aggregate/rank **without collapsing rows**; `FUNC() OVER (PARTITION BY ... ORDER BY ... ROWS BETWEEN ...)`.
- **Latest-per-key** = `ROW_NUMBER() OVER (PARTITION BY key ORDER BY ts DESC)` filtered to `= 1` in a **subquery**.
- **`ROW_NUMBER` / `RANK` / `DENSE_RANK`** = unique / gaps-on-ties / no-gaps.
- **Running total** = `SUM() OVER (ORDER BY ...)`; **moving avg** = add `ROWS BETWEEN n PRECEDING AND CURRENT ROW`.
- **`LAG`/`LEAD`** = previous/next row → deltas & sessionization.
- **Athena has no `QUALIFY`** → subquery. **`try_cast`** for dirty data. **Anti-join** for "what's missing".

---

## Common gotchas

- **Window function in `WHERE`** → syntax error. Wrap in a subquery/CTE and filter outside.
- **`RANK` vs `ROW_NUMBER` on ties** — using `ROW_NUMBER` for "top N" silently drops tied rows.
- Forgetting **`ORDER BY` inside `OVER`** for running totals — without it the result is undefined/whole-partition.
- **`ROWS` vs `RANGE`** frames differ on ties; default to `ROWS` unless you specifically want value-based ranges.
- Assuming **`QUALIFY`** works in Athena — it doesn't.

---

## Check yourself

1. How is a window function different from `GROUP BY`?
2. Write the latest-record-per-key query, and explain why the subquery is required.
3. Give the tie behavior of all three ranking functions.
4. Write a 7-day moving average with a frame.
5. How would you find orders that have no matching shipment (two ways)?
6. What's the Athena catch with `QUALIFY`?
