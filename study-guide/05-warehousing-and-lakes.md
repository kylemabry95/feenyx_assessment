# 05 — Warehouses & Lakes (Redshift, Lake Formation, Table Formats)

Prereqs: [00 — Fundamentals](00-data-engineering-fundamentals.md) (lake vs warehouse), [03 — S3](03-amazon-s3.md), [01 — Glue](01-aws-glue.md).

This chapter covers three things that make a data lake behave like a real, governed, transactional warehouse: **Redshift** (the warehouse), **Lake Formation** (governance), and **open table formats** (transactions on S3).

---

## Amazon Redshift — the data warehouse

### In plain English

**Redshift is a database purpose-built for analytics** — fast aggregate queries over billions of rows. Unlike Athena (which reads files on demand), Redshift **loads and stores data in its own optimized format** for maximum query speed and high concurrency (many users at once).

### How it works

- It's an **MPP (Massively Parallel Processing) columnar** database. "MPP" = the work is split across many nodes that compute in parallel. "Columnar" = stores data by column (like Parquet) for fast analytics.
- **Distribution style** — how rows are spread across nodes. This is a key tuning knob:
  - **KEY** — rows with the same value of a chosen column go to the same node (great for joins on that column).
  - **EVEN** — spread rows evenly, round-robin (good when no obvious join key).
  - **ALL** — copy the whole (small) table to every node (great for small dimension tables so joins need no data movement).
  - **AUTO** — let Redshift decide.
- **Sort keys** — keep rows physically ordered by a column (usually a date) so range queries skip blocks. Similar idea to partitioning.
- **`VACUUM`** reclaims space and re-sorts after lots of updates/deletes; **`ANALYZE`** refreshes the statistics the query planner uses. Both are housekeeping you run to keep performance up.
- **Redshift Spectrum** — query data *in S3* directly from Redshift, using the **Glue Data Catalog**. Lets you join warehouse tables with lake data without loading it.
- **RA3 nodes** — **separate compute from storage**, so you scale each independently and pay for what you use. The modern node type.

### When to use Redshift vs Athena

- **Athena** — ad-hoc, occasional queries; pay per scan; no infrastructure. Great for exploration.
- **Redshift** — steady, high-concurrency BI workloads (many dashboards, many users), complex joins, predictable performance. Worth the always-on cost when query volume is high.

---

## Lake Formation — governance for the lake

### In plain English

Securing a data lake with raw S3 permissions is painful — you'd write bucket policies for every folder. **Lake Formation is a governance layer that lets you grant access at the database/table/column/row level, like a real database**, instead of wrangling S3 paths.

### How it works

- Sits **on top of the Glue Data Catalog.** You register your S3 locations with Lake Formation, then grant permissions with familiar `GRANT SELECT ON table TO principal` semantics.
- **Fine-grained access control:** **column-level** (hide the SSN column from analysts), **row-level** (a user only sees their region's rows), and **cell-level** security.
- **LF-Tags (tag-based access control, TBAC):** tag tables/columns (e.g., `classification=PII`) and grant access to *tags* rather than individual objects. Scales far better than per-object grants.
- **Cross-account sharing** — share catalog data with other AWS accounts securely.
- It **replaces raw S3 IAM policies** with database/table-level grants that all the analytics tools (Athena, Redshift Spectrum, Glue, EMR) enforce consistently.

> Conceptually, **Lake Formation ≈ Unity Catalog** in the Databricks world (governance + fine-grained access over your data assets).

---

## Open table formats — ACID on S3

### The problem they solve

Plain files in S3 (even Parquet) have no concept of a **transaction.** If you're rewriting a partition and a query runs mid-write, it sees a broken half-state. You also can't easily **update or delete individual rows**, undo a mistake, or evolve the schema safely. Data lakes needed database-like guarantees. **Open table formats add a transaction/metadata layer on top of Parquet files** to provide exactly that.

### What they give you (all three)

- **ACID transactions** — writes are all-or-nothing; readers never see partial writes.
- **Time travel** — query the table as it was at a past point ("show me yesterday's version"). Great for audits and undoing mistakes.
- **Schema evolution** — add/rename/change columns safely.
- **Row-level updates/deletes/merges** — `UPDATE`, `DELETE`, `MERGE` (upsert) on a lake, which raw Parquet can't do.

### The three formats

- **Apache Iceberg** — the emerging standard; **Athena and Glue support it natively.** If AWS-native, this is usually the default choice.
- **Apache Hudi** — strong at streaming upserts and incremental pulls.
- **Delta Lake** — originated at Databricks; the default in the Databricks world.

**AWS support:** Athena/Glue favor **Iceberg**; **Glue 4.0+ supports all three** (Iceberg, Hudi, Delta). For this assessment's AWS-native framing, lead with **Iceberg**.

---

## Key facts to memorize

- **Redshift** = MPP columnar warehouse. Distribution styles **KEY/EVEN/ALL/AUTO**, **sort keys**, **`VACUUM`/`ANALYZE`** housekeeping. **Spectrum** queries S3 via Glue Catalog. **RA3** separates compute/storage.
- **Lake Formation** = governance on the Glue Catalog: column/row/cell security, **LF-Tags (TBAC)**, cross-account sharing. Replaces raw S3 IAM with table-level grants. ≈ Unity Catalog.
- **Open table formats (Iceberg/Hudi/Delta)** = **ACID + time travel + schema evolution + row-level updates** on S3. Athena/Glue favor **Iceberg**; Glue 4.0+ supports all three.

---

## Common gotchas

- **Redshift `ALL` distribution on a big table** wastes huge space — it's only for small dimensions.
- Skipping **`VACUUM`/`ANALYZE`** lets Redshift performance rot over time.
- Assuming a **plain Parquet lake supports `UPDATE`/`DELETE`** — it doesn't; you need a table format for that.
- Mixing table formats randomly — pick one (Iceberg for AWS-native) and standardize.

---

## Databricks translation

| Databricks | AWS-native |
|---|---|
| Unity Catalog | Glue Catalog + Lake Formation |
| Delta Lake tables | Iceberg/Hudi/Delta on S3 (Athena favors Iceberg) |
| Databricks SQL warehouse | Redshift / Athena |

---

## Check yourself

1. When would you choose Redshift over Athena?
2. What does the `ALL` distribution style do, and when is it appropriate?
3. What problem do open table formats solve that plain Parquet can't?
4. Which table format is the AWS-native default, and why?
5. What are LF-Tags and why do they scale better than per-object grants?
