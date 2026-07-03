# 01 — AWS Glue (ETL)

Prereqs: [00 — Fundamentals](00-data-engineering-fundamentals.md), [03 — S3](03-amazon-s3.md). Glue is how AWS transforms and catalogs the data sitting in S3.

---

## In plain English

**AWS Glue is a "serverless" service that runs your data-cleaning code and keeps a catalog of what data you have.** "Serverless" means you don't rent or manage any servers — you hand Glue your transformation logic, and AWS spins up compute, runs it, and shuts it down. You pay only for the time it runs.

Glue is really several tools under one name:

1. **Glue Data Catalog** — a directory of all your tables (what columns, what types, where the files are).
2. **Crawlers** — robots that scan your data and fill in the catalog automatically.
3. **Glue Jobs** — the actual ETL code (usually PySpark) that transforms data.
4. **Glue Workflows / Triggers** — lightweight orchestration to chain the above.
5. **Glue Data Quality / Studio** — add-ons for validation and visual editing.

---

## Why it exists

Before Glue, to run Spark ETL you had to provision and manage a cluster (EMR), keep it patched, and pay for it even when idle. Glue removes all of that: it runs **Apache Spark under the hood** but you never see the cluster. It also solves the "what data do I even have?" problem with a central catalog that every other AWS analytics tool can read.

---

## How it actually works

### Pricing unit: the DPU

Glue bills per **DPU-hour**. A **DPU (Data Processing Unit) = 4 vCPUs + 16 GB RAM.** Your job uses some number of DPUs (workers) for some time; that's your bill. More DPUs = faster but more expensive. Right-sizing DPUs is a cost-tuning lever.

### The Glue Data Catalog

The catalog is a **Hive-compatible metastore** — a database *about* your data. For each table it records: column names, types, the S3 location, the file format, and partitions. Crucially, **it stores metadata only, not the data itself** (the data stays in S3).

Why it's central: **Athena, Redshift Spectrum, EMR, and Lake Formation all read from the same catalog.** Define a table once, query it from everywhere. There is **one catalog per region per account.**

### Crawlers

A **crawler** points at an S3 path (or a JDBC database), scans the files, **infers the schema** (guesses columns and types), and **creates or updates the catalog table** — including discovering partitions. Run them on a schedule or on demand. Use **exclusion patterns** to skip files you don't want cataloged (e.g., temp files, `_SUCCESS` markers).

> You don't always need a crawler. If you already know your schema, you can define tables directly (or via Athena DDL / partition projection). Crawlers shine when schemas are unknown or changing.

### Glue Jobs

The workhorse. Three flavors:

- **Spark jobs** (PySpark or Scala) — full distributed processing for big data. The default.
- **Spark Streaming jobs** — process Kinesis/Kafka streams continuously.
- **Python Shell jobs** — lightweight, **no Spark**, just a Python environment. Great for small tasks: calling an API, running a bit of pandas, light orchestration. Cheaper than spinning up Spark.

Version cheat sheet: **Glue 4.0 = Spark 3.3; Glue 5.0 = Spark 3.5.**

### DynamicFrame vs DataFrame (a signature Glue concept)

Spark's normal data structure is a **DataFrame**, which requires a fixed, known schema. Glue adds its own structure called a **DynamicFrame**:

- A **DynamicFrame** is **schema-flexible** — each record self-describes its fields. It can handle messy data where records have different or inconsistent types, using special **"choice" types** (a column that's sometimes an int, sometimes a string). It's resilient to the kind of dirty data you get from real sources.
- A **DataFrame** is **faster** and gives you the full, familiar Spark SQL API, but it needs a consistent schema.

You convert freely: `dynamicFrame.toDF()` to get a DataFrame, `DynamicFrame.fromDF(df, glueContext, "name")` to go back. **Common pattern:** read messy source as a DynamicFrame → `.toDF()` → do your real transformations with the DataFrame API → convert back only if a Glue-specific sink needs it.

> One-liner to remember: **DynamicFrames are resilient to messy data; DataFrames are faster.**

### Job Bookmarks (incremental processing)

By default a job would reprocess *all* the data every run. **Job bookmarks** make Glue **remember what it already processed**, so each run only picks up *new* files/rows. This is Glue's answer to incremental loads. (If you know Databricks: bookmarks ≈ Auto Loader / streaming checkpoints.)

### Glue Workflows

Lightweight orchestration **inside Glue**: chain crawlers + jobs + triggers into a DAG. Good when your whole pipeline is Glue and you don't want the weight of Step Functions or Airflow. For anything beyond simple Glue-only flows, reach for **Step Functions or MWAA** (see [chapter 08](08-orchestration-and-iac.md)).

### Glue Data Quality

Rule-based validation built on **Deequ** (Amazon's open-source DQ library). You write rules in **DQDL** (Data Quality Definition Language), e.g.:

```
Rules = [
  Completeness "customer_id" > 0.95,
  IsUnique "order_id",
  ColumnValues "status" in ["active","closed","pending"]
]
```

Use it to **gate promotion between zones** — data only moves bronze→silver if it passes. (Great Expectations is a popular third-party alternative.)

### Glue Studio

A **visual, drag-and-drop ETL editor** that generates PySpark for you. Useful for simpler jobs or non-coders; senior engineers usually write code directly.

---

## Key facts to memorize

- Glue = **serverless Spark ETL**, billed per **DPU-hour** (1 DPU = 4 vCPU + 16 GB).
- **Data Catalog** = central Hive metastore, metadata only, **one per region per account**, shared by Athena/Redshift Spectrum/EMR/Lake Formation.
- **Crawlers** infer schema and populate the catalog; use exclusion patterns.
- **Job types:** Spark, Spark Streaming, **Python Shell (no Spark, lightweight)**.
- **DynamicFrame** = messy-data-resilient, self-describing, "choice" types; **DataFrame** = faster. Convert with `.toDF()` / `fromDF()`.
- **Job bookmarks** = incremental processing (only new data).
- **Glue Workflows** = lightweight Glue-only orchestration.
- **Glue Data Quality** = DQDL rules on Deequ; **Glue Studio** = visual editor.
- Versions: **4.0 → Spark 3.3, 5.0 → Spark 3.5.**

---

## Common gotchas

- Crawlers can **mis-infer types** (everything as string, or splitting one table into many). For stable schemas, defining tables explicitly or using partition projection is often more reliable.
- DynamicFrames are convenient but **slower**; don't leave everything as a DynamicFrame — convert to DataFrame for heavy transforms.
- Forgetting **`job.commit()`** at the end means job bookmarks won't advance, and you'll reprocess data.
- Glue is Spark — the **small files problem** and **data skew** apply (see [chapter 09](09-pyspark.md)).

---

## Databricks translation (for your background)

| Databricks | Glue equivalent |
|---|---|
| Unity Catalog | Glue Data Catalog + Lake Formation |
| Auto Loader / checkpoints | Job bookmarks |
| Databricks Jobs/Workflows | Glue Workflows / Step Functions / MWAA |
| Notebook Spark code | Glue Spark job (PySpark) |

---

## Check yourself

1. What does "serverless" mean in the context of Glue, and what are you billed for?
2. When would you pick a Python Shell job over a Spark job?
3. Explain DynamicFrame vs DataFrame in one sentence each.
4. What problem do job bookmarks solve?
5. Which four services read from the Glue Data Catalog?
