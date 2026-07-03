# 02 — Amazon Athena (Querying S3)

Prereqs: [03 — S3](03-amazon-s3.md), [01 — Glue](01-aws-glue.md). Athena is how you run SQL directly on files in your data lake.

---

## In plain English

**Athena lets you run ordinary SQL queries against files sitting in S3 — no database to load, no servers to manage.** You point it at a table (defined in the Glue Data Catalog), write `SELECT ...`, and Athena reads the underlying S3 files and returns results. You pay **per amount of data scanned**, not for idle time.

It's built on **Presto/Trino**, a fast distributed SQL engine.

---

## Why it exists

Sometimes you just want to ask a question of raw data without the ceremony of loading it into a warehouse. Athena makes S3 queryable on demand. Because it's serverless and pay-per-scan, it's perfect for **ad-hoc exploration** and moderate analytics. The trade-off: since you pay per byte scanned, **how you store the data enormously affects your bill.**

---

## How it actually works

1. Your data lives in S3 as files (ideally Parquet).
2. A **table definition** in the **Glue Data Catalog** tells Athena where the files are, their format, and the schema.
3. You run SQL. Athena reads only what it must from S3, computes the result, and writes results back to an S3 "results" location.
4. AWS bills you **$5 per terabyte scanned** (the number to remember).

The whole game of using Athena well is **scanning less data.**

---

## The cost/performance optimization checklist (THE classic exam question)

Memorize this ordered list — it comes up constantly:

1. **Use columnar formats (Parquet/ORC).** A columnar file lets Athena read only the columns your query needs instead of every column. Biggest single win.
2. **Compress the data** (Snappy for Parquet). Fewer bytes on disk = fewer bytes scanned = cheaper.
3. **Partition the data** (e.g., `s3://bucket/table/year=2026/month=07/`) and **filter on the partition keys** in your `WHERE` clause. Athena skips partitions it doesn't need — **partition pruning**.
4. **Use partition projection** for high-partition tables. Instead of storing every partition in the catalog and running slow `MSCK REPAIR TABLE` (or a crawler) to discover them, you tell Athena the *pattern* of partitions (e.g., dates from 2020-01-01 onward) and it calculates them on the fly. Faster, no crawler dependency.
5. **Bucket high-cardinality join keys** so joins read fewer files.
6. **Know what does NOT help:** **`LIMIT` alone does not reduce scan cost** — Athena may still scan the whole file to satisfy the query. Only columnar formats + partitioning + compression truly cut the bytes scanned.

> If you remember one thing: **Parquet + Snappy + partition-and-filter-by-date** is 90% of Athena cost optimization.

---

## CTAS — CREATE TABLE AS SELECT

```sql
CREATE TABLE curated.orders_parquet
WITH (format = 'PARQUET', partitioned_by = ARRAY['order_date'])
AS SELECT * FROM raw.orders_csv;
```

**CTAS runs a query and writes the results back to S3 as a new table** — commonly used to **convert CSV/JSON to partitioned Parquet in a single SQL statement.** It's an easy way to do lightweight ETL entirely in Athena, and to repartition data.

---

## Workgroups

**Athena workgroups** separate different query workloads. With them you can:

- Enforce a **per-query data-scan limit** (a guardrail against a `SELECT *` that scans 50 TB and costs a fortune).
- **Tag and track costs** by team or project.
- Set the results output location and enforce encryption.

Use workgroups to control spend and isolate teams — a good governance talking point.

---

## Federated queries

Athena can query data **outside** S3 — RDS, DynamoDB, Redshift, on-prem databases — using **Lambda-based connectors.** This lets one SQL query join lake data with operational database data. Slower than native S3 queries, but powerful when you need to combine sources without moving data.

---

## Athena SQL dialect notes (bites people in coding questions)

- **No `QUALIFY`** — Trino/Athena doesn't support `QUALIFY`, so to filter on a window function you must wrap it in a **subquery** and filter the outer query (`... ) WHERE rn = 1`).
- **`UNNEST`** flattens arrays into rows (Athena's version of `explode`).
- **`try_cast()`** casts without throwing on bad values (returns NULL instead) — essential for dirty data.
- **`date_trunc('month', ts)`**, **CTEs (`WITH`)**, and **anti-joins** (`LEFT JOIN ... WHERE right.id IS NULL` or `NOT EXISTS`) are all standard.

See [chapter 10](10-sql-window-functions.md) for the full window-function patterns.

---

## Key facts to memorize

- Athena = **serverless SQL over S3**, built on **Presto/Trino**, billed **$5/TB scanned**.
- Reads table definitions from the **Glue Data Catalog**.
- Optimize by **scanning less**: Parquet/ORC → compress → partition & filter → partition projection → bucketing. **`LIMIT` doesn't cut scan cost.**
- **CTAS** = convert/repartition to Parquet in one statement.
- **Workgroups** = per-query scan limits + cost tagging + isolation.
- **Federated queries** = query non-S3 sources via Lambda connectors.
- **No `QUALIFY`** — use a subquery.

---

## Common gotchas

- Querying **CSV instead of Parquet** silently costs 10x. Convert first (CTAS).
- Forgetting to **filter on the partition key** means no pruning — you scan everything even though the data is partitioned.
- Too many small files → slow queries and higher cost. Compact.
- Not setting a **workgroup scan limit** means one bad query can cost hundreds of dollars.

---

## Databricks translation

| Databricks | AWS-native |
|---|---|
| Databricks SQL / Genie | Athena (+ QuickSight for dashboards) |
| DBSQL warehouse | Athena or Redshift |

---

## Check yourself

1. What are you billed for in Athena, and what's the headline price?
2. List the optimization checklist in order. Why doesn't `LIMIT` help?
3. What does partition projection replace, and why is it better?
4. What does CTAS do in one sentence?
5. You need to filter rows using a window function in Athena — what's the catch?
