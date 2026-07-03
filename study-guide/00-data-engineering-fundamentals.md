# 00 — Data Engineering Fundamentals

Read this first. Every other chapter assumes you know these words. None of it is AWS-specific — it's the mental model of the whole field.

---

## What is a data engineer, really?

A **data engineer builds the plumbing that moves data from where it's created to where it's used.**

- Data gets *created* by apps, sensors, APIs, spreadsheets, databases.
- Data gets *used* by analysts (dashboards), data scientists (ML models), and executives (reports).
- In between, someone has to collect it, clean it, reshape it, store it cheaply, and keep it flowing reliably. That's the data engineer.

Analogy: if data is water, the data engineer builds the pipes, filters, reservoirs, and pressure gauges. Analysts and scientists just turn on the tap.

---

## The core verbs: ETL and ELT

Almost all data work is some version of **Extract → Transform → Load**.

- **Extract** — pull data out of a source (a database, an API, files).
- **Transform** — clean and reshape it (remove duplicates, fix dates, join tables, aggregate).
- **Load** — write it into a destination where people can query it.

**ETL vs ELT** is just about *when* you transform:

- **ETL** — transform *before* loading. Classic approach; you clean the data, then store the clean version.
- **ELT** — load the raw data first, then transform it *inside* the destination (often a warehouse). Modern cloud approach, because storage is cheap and warehouses are powerful. Loading raw data first means you never lose the original.

> **Exam framing:** modern cloud data stacks lean ELT — dump raw data cheaply into S3/a warehouse, transform later. Keeping the raw copy is a feature, not waste.

---

## Batch vs streaming

Two ways data moves:

- **Batch** — process a chunk of data on a schedule. "Every night at 2am, load yesterday's orders." Simple, cheap, high-latency (you wait until the batch runs).
- **Streaming** — process each record as it arrives, continuously. "The moment a payment happens, update the fraud model." Complex, more expensive, low-latency (near real-time).

Choose batch unless the business genuinely needs fresh-to-the-second data. Most work is batch.

---

## Structured, semi-structured, unstructured

- **Structured** — fits neatly in rows and columns. A database table, a CSV. Every row has the same fields.
- **Semi-structured** — has *some* structure but it's flexible. JSON, XML. Records can have different fields; things can be nested.
- **Unstructured** — no inherent table shape. PDFs, images, raw text, audio.

Data engineers spend most of their time turning semi-structured mess (JSON from APIs) into clean structured tables.

---

## Data lake vs data warehouse vs lakehouse

This trips up beginners constantly. The difference is about **structure and cost.**

| | Data Lake | Data Warehouse | Lakehouse |
|---|---|---|---|
| Stores | Everything, any format, raw | Cleaned, structured tables | Both — raw files *with* table features |
| Cost | Very cheap (object storage) | More expensive (compute + storage) | Cheap storage, warehouse-like features |
| Structure | Schema-on-read (figure out structure when you query) | Schema-on-write (define structure before loading) | Schema-on-read + ACID transactions |
| Example | S3 full of Parquet/JSON | Redshift, Snowflake, BigQuery | S3 + Iceberg/Delta tables |

- **Data lake** = a big cheap bucket (in AWS, that's **S3**). You throw anything in. Flexible but easy to turn into a "data swamp" if ungoverned.
- **Data warehouse** = a database optimized for analytics queries over structured data (in AWS, **Redshift**). Fast, but you must structure data first and pay for it.
- **Lakehouse** = the modern hybrid. Store cheap files in S3, but add a "table format" (Iceberg/Delta/Hudi) that gives you database-like features (transactions, updates, time travel) on top of those files. This is where the industry is heading.

**Schema-on-read vs schema-on-write** — a lake lets you dump data now and decide its structure later (schema-on-read). A warehouse forces you to define the structure before loading (schema-on-write).

---

## The medallion / zone architecture

The single most important design pattern you'll be asked about. A data lake is organized into **layered zones**, each cleaner than the last:

- **Bronze / Raw** — data exactly as it arrived, untouched. If everything downstream breaks, you can rebuild from here. Never edit it.
- **Silver / Cleansed** — deduplicated, typed, validated, standardized. The "single source of truth" tables.
- **Gold / Curated** — business-ready aggregates and features. What dashboards and ML models actually read.

Data only flows **upward**, and quality checks gate each promotion (bad data isn't allowed into gold). "Medallion" (bronze/silver/gold) is Databricks vocabulary; "raw/cleansed/curated zones" is the AWS-native phrasing for the exact same idea. **Say both names** in an interview.

---

## File formats: why Parquet beats CSV

How you store data on disk hugely affects cost and speed.

- **Row-based formats (CSV, JSON)** store data one whole record at a time. To read one column, you still read every row entirely. Human-readable, but slow and big for analytics.
- **Columnar formats (Parquet, ORC)** store each *column* together. To sum one column, you read only that column's data — skipping the rest. Also compresses far better (similar values sit next to each other).

**Parquet is the default choice for analytics.** It's columnar, compressed, and every AWS analytics tool reads it natively. Switching CSV → Parquet often cuts query cost 10x because you scan less data.

- **Compression** — Snappy is the usual pick with Parquet (fast, splittable). Gzip compresses smaller but is slower.
- **NDJSON / JSONL** — "newline-delimited JSON," one JSON object per line. Common for landing raw semi-structured data before converting to Parquet.

---

## Partitioning: the #1 performance lever

**Partitioning = physically splitting data into folders by a column's value** so queries can skip the folders they don't need.

Example layout:

```
s3://bucket/orders/year=2026/month=07/day=03/file.parquet
```

If someone queries "orders in July 2026," the engine reads only the `year=2026/month=07/` folder and *ignores everything else*. This is called **partition pruning**, and it's the biggest cost/speed win in the analytics world.

- Partition on columns people **filter by** (date is the classic).
- Don't over-partition — millions of tiny folders (e.g., partitioning by user_id) create the "small files problem" and slow everything down.

**Bucketing** is a cousin: it splits data into a fixed number of files by hashing a high-cardinality column (like a join key), so joins and lookups touch fewer files.

---

## The small files problem

Analytics engines (Spark, Athena) are efficient with a *few large* files and terrible with *millions of tiny* ones — each file has overhead. Ideal file size is roughly **128 MB to 1 GB**. When streaming or frequent writes create tons of small files, you run **compaction** jobs that merge them into big ones. Expect to be asked about this.

---

## Schema and schema evolution

- **Schema** = the structure of your data: column names and types.
- **Schema evolution** = what happens when that structure changes over time (a new column appears, a type changes). Good pipelines handle this gracefully instead of crashing. Modern table formats (Iceberg/Delta/Hudi) support schema evolution natively.

---

## Idempotency (a word you must be able to say confidently)

An operation is **idempotent** if running it twice produces the same result as running it once. Pipelines fail and get retried all the time, so they must be safe to re-run without creating duplicates or double-counting. "Idempotent and resumable" is a phrase that signals seniority — sprinkle it into design answers.

---

## Orchestration

Real pipelines have many steps that depend on each other ("clean the data *after* it lands, aggregate *after* it's clean"). An **orchestrator** schedules these steps, runs them in the right order, retries failures, and alerts you. The steps form a **DAG** (Directed Acyclic Graph — a flowchart with no loops). Airflow is the most famous orchestrator; AWS's managed version is **MWAA**.

---

## Infrastructure as Code (IaC)

Instead of clicking buttons in a cloud console to create resources, you **write the configuration in code** (e.g., Terraform) and apply it. Benefits: repeatable, reviewable, version-controlled, and you can rebuild an entire environment from scratch. "Everything is Terraform" is a senior expectation.

---

## Governance and lineage

- **Governance** — controlling who can access what data, and cataloging what data exists. Critical for security and compliance.
- **Data lineage** — the ability to trace where a piece of data came from and what transformed it. "This dashboard number traces back to *these* source tables through *these* jobs." Important for debugging and audits.

---

## Check yourself

1. What's the difference between ETL and ELT, and why does the cloud favor ELT?
2. Why is Parquet cheaper to query than CSV?
3. What does partition pruning do, and what column would you usually partition on?
4. Name the three medallion zones and what each contains.
5. What does "idempotent" mean and why does a pipeline need to be?
6. When would you choose streaming over batch?

If you can answer all six in a sentence each, you're ready for the AWS-specific chapters.
