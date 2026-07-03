# 13 — Data Quality

Prereqs: [00 — Fundamentals](00-data-engineering-fundamentals.md), [01 — Glue](01-aws-glue.md) (Glue Data Quality), [12 — Pipeline Design](12-pipeline-design.md).

"How do you ensure data quality?" is one of the most likely long-form questions. It's also what separates a pipeline that people *trust* from one they don't.

---

## In plain English

**Data quality means the data is correct, complete, and trustworthy enough to make decisions on.** Bad data is worse than no data — it produces confidently wrong dashboards and broken ML models. Your job is to catch problems *early* and stop bad data from spreading downstream.

The guiding principle: **fail closed.** If data is bad, it should be quarantined and *not* promoted — never silently passed to the gold layer where a dashboard will show it.

---

## The dimensions of data quality (the vocabulary)

Know these terms — they're what DQ rules check:

- **Completeness** — are required fields present / not null? (e.g., "95% of `customer_id` must be non-null")
- **Uniqueness** — no unexpected duplicates. (e.g., "`order_id` is unique")
- **Validity** — values conform to rules/formats. (e.g., "`status` is one of active/closed/pending", "email matches a pattern")
- **Accuracy** — values match reality/source of truth.
- **Consistency** — values agree across tables/systems (no contradictions).
- **Timeliness / Freshness** — data is recent enough. (e.g., "the latest record is < 24h old")
- **Referential integrity** — foreign keys actually exist in the referenced table (every `order.customer_id` exists in `customers`).

---

## The 5-part framework (the long-form answer)

Structure your "how do you ensure data quality?" answer around these five stages:

### 1. Validation at ingestion
Catch problems as data enters:
- **Schema enforcement** — reject records that don't match the expected structure.
- **Typed casts** — `try_cast` dirty values; malformed ones become null instead of crashing.
- **Quarantine / dead-letter path** — bad records go to a separate location for inspection, not into the pipeline. Nothing is silently dropped.

### 2. Rule-based checks between zones
Before promoting bronze→silver→gold, run DQ rules:
- **Glue Data Quality (DQDL, built on Deequ)** or **Great Expectations** (popular third-party).
- Check completeness, uniqueness, referential integrity, freshness, valid ranges.
- Example DQDL: `Completeness "email" > 0.95`, `IsUnique "order_id"`, `ColumnValues "amount" >= 0`.

### 3. Reconciliation against source
Prove nothing was lost or duplicated:
- **Row-count checks** — does the target count match the source count (± expected changes)?
- **Control totals** — do sums of key financial columns match the source system?

### 4. Monitoring & alerting
- Emit **DQ metrics** to CloudWatch; alarm when they breach thresholds.
- Track quality **trends over time** — a slowly rising null rate is an early warning.
- Alert a human on failure; don't let bad data pass silently.

### 5. Fail-closed promotion
- **Bad data never reaches gold.** If checks fail, block the promotion, quarantine the batch, and alert.
- The gold layer is sacred — everything reading it (dashboards, ML) assumes it's clean.

---

## Where DQ fits in the architecture

```
Source → [ingest + schema check + quarantine] → Bronze
       → [DQ rules gate] → Silver
       → [DQ rules + reconciliation gate] → Gold  → dashboards / ML
                    │
                    └── fail → quarantine + alert (never promote)
```

Each arrow between zones is a **quality gate.** Data only moves up if it passes.

---

## Tools recap

- **Glue Data Quality** — AWS-native, rules in **DQDL**, built on **Deequ**. Integrates into Glue jobs.
- **Deequ** — Amazon's open-source Spark DQ library (the engine under Glue DQ).
- **Great Expectations** — widely used third-party framework; expressive "expectations," data docs, works outside AWS too.
- **dbt tests** — if using dbt for transformations, built-in `not_null`, `unique`, `accepted_values`, `relationships` tests.

---

## Key facts to memorize

- Guiding principle: **fail closed** — bad data is quarantined, never promoted.
- **DQ dimensions:** completeness, uniqueness, validity, accuracy, consistency, timeliness/freshness, referential integrity.
- **5-part framework:** (1) validation at ingestion + quarantine, (2) rule-based checks between zones, (3) reconciliation vs source counts, (4) monitoring/alerting on DQ metrics, (5) fail-closed promotion.
- Tools: **Glue Data Quality (DQDL/Deequ)**, **Great Expectations**, dbt tests.

---

## Common gotchas

- **Silently dropping bad rows** — always quarantine so you can investigate; dropping hides data loss.
- **No reconciliation** — passing DQ rules but losing half the rows to a bad join goes unnoticed without count checks.
- **Checking only at the end** — catch problems at ingestion, not after they've spread.
- **Alerting on everything** — tune thresholds so alerts mean something; noisy alerts get ignored.

---

## Anchor it in your experience

Cite the **USASpending bronze→silver cleaning work (310+ columns)** as concrete scale, and the **medallion promotion gates** in the NASA EDP pipelines as proof you've built fail-closed quality controls, not just talked about them.

---

## Check yourself

1. What does "fail closed" mean for data quality?
2. Name five data-quality dimensions and give a rule for each.
3. Walk through the 5-part DQ framework.
4. Why is reconciliation (row-count checks) needed on top of rule-based checks?
5. What's the difference between Glue Data Quality, Deequ, and Great Expectations?
