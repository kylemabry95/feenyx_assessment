# Senior Data Engineer — Skills Assessment Study Guide

**Assessment format:** 2 multiple choice · 2 coding questions · 2 long-form responses (Feenyx platform)

This guide is organized around the assessment format, then deep-dives into each JD area. Since your daily driver is Databricks on GovCloud rather than native AWS Glue, there's a translation table at the end mapping what you already know to the Glue/Athena vocabulary this assessment will use.

---

## Part 1: Assessment Strategy

**Multiple choice** will almost certainly test AWS service facts and "which service for which job" scenarios. Memorize the rapid-fire facts in Part 2.

**Coding questions** will be Python and/or SQL. Expect either (a) a PySpark/pandas transformation task, (b) a SQL window-function problem, or (c) an API ingestion + cleansing task. Patterns in Part 3.

**Long-form responses** are where you win. They'll ask you to design a pipeline or data platform end-to-end. Use the frameworks in Part 4 and ground answers in your real NASA EDP work — medallion architecture, Unity Catalog governance, GuardDuty centralization, FedRAMP compliance. That's exactly the "Federal/DoD background" they list as preferred.

---

## Part 2: Multiple Choice Prep — Rapid-Fire Service Facts

### AWS Glue
- **What it is:** Serverless ETL service running Apache Spark under the hood. You pay per DPU-hour (Data Processing Unit = 4 vCPU + 16 GB).
- **Glue Data Catalog:** Central Hive-compatible metastore. Athena, Redshift Spectrum, EMR, and Lake Formation all read from it. One catalog per region per account.
- **Crawlers:** Scan S3 (or JDBC sources), infer schema, and create/update catalog tables. Can run on schedule or on demand. Use exclusion patterns to skip files.
- **Glue Jobs:** Spark (PySpark/Scala), Spark Streaming, or Python Shell (lightweight, no Spark). Glue 4.0 = Spark 3.3; Glue 5.0 = Spark 3.5.
- **DynamicFrame vs DataFrame:** DynamicFrame is Glue's schema-flexible abstraction — each record self-describes, handles inconsistent schemas ("choice" types). Convert with `.toDF()` / `fromDF()`. DataFrames are faster; DynamicFrames are more resilient to messy data.
- **Job bookmarks:** Glue's incremental-processing mechanism — tracks processed data between runs so you only process new files. (Analogous to Auto Loader/checkpoints in your Databricks world.)
- **Glue Workflows:** Orchestrate crawlers + jobs + triggers as a DAG (lightweight alternative to Step Functions/Airflow/MWAA).
- **Glue Data Quality:** Rule-based DQ (DQDL language) built on Deequ. Rules like `Completeness "col" > 0.95`, `IsUnique "id"`.
- **Glue Studio:** Visual ETL editor generating PySpark.

### Amazon Athena
- **What it is:** Serverless, Presto/Trino-based interactive SQL over S3. Pay per data scanned ($5/TB).
- **Cost/performance optimization (classic exam question):**
  1. Convert to columnar formats (Parquet/ORC) — scans only needed columns
  2. Compress (Snappy for Parquet)
  3. Partition data (e.g., `s3://bucket/table/year=2026/month=07/`) and filter on partition keys
  4. Use partition projection to avoid slow `MSCK REPAIR TABLE` / crawler dependency
  5. Bucket high-cardinality join keys
  6. `LIMIT` doesn't reduce scan cost by itself — partitioning and columnar formats do
- **CTAS (CREATE TABLE AS SELECT):** Converts/repartitions data into Parquet in one SQL statement.
- **Athena workgroups:** Separate query workloads, enforce per-query scan limits, tag costs.
- **Federated queries:** Query RDS, DynamoDB, etc. via Lambda-based connectors.

### Amazon S3
- **Storage classes:** Standard → Intelligent-Tiering → Standard-IA → One Zone-IA → Glacier Instant/Flexible/Deep Archive. Intelligent-Tiering = automatic, no retrieval fees.
- **Consistency:** Strong read-after-write consistency for all operations (since Dec 2020).
- **Performance:** 3,500 PUT / 5,500 GET requests per second **per prefix** — parallelize with prefixes.
- **Security:** Bucket policies (resource-based), SSE-S3 vs SSE-KMS vs SSE-C encryption, Block Public Access, VPC endpoints (gateway endpoints for S3 are free), Object Lock for WORM/compliance.
- **Lifecycle policies:** Transition + expiration rules; also abort incomplete multipart uploads.
- **Event notifications:** S3 → EventBridge/SQS/SNS/Lambda — the trigger backbone of event-driven pipelines.

### Streaming: Kinesis vs Kafka (MSK)
- **Kinesis Data Streams:** Shards are the throughput unit — 1 MB/s or 1,000 records/s in, 2 MB/s out per shard. Retention 24h default, up to 365 days. On-demand mode auto-scales. Enhanced fan-out gives each consumer dedicated 2 MB/s.
- **Kinesis Data Firehose:** Fully managed *delivery* — near-real-time (buffering by size/time) to S3, Redshift, OpenSearch, Splunk. No shard management, no custom consumers. Can invoke Lambda for inline transformation and convert to Parquet.
- **MSK (Managed Kafka):** Choose when you need Kafka ecosystem compatibility, longer retention, exactly-once semantics, or existing Kafka tooling. More ops burden than Kinesis even when managed.
- **Rule of thumb for MCQs:** "simplest way to land streaming data in S3 as Parquet" → **Firehose**. "Custom consumers / replay / ordering per key" → **Kinesis Data Streams**. "Kafka APIs required" → **MSK**.

### Warehousing & Lakes
- **Redshift:** MPP columnar warehouse. Distribution styles (KEY, EVEN, ALL, AUTO), sort keys, `VACUUM`/`ANALYZE`. Redshift Spectrum queries S3 via Glue Catalog. RA3 nodes separate compute/storage.
- **Lake Formation:** Governance layer on Glue Catalog — column/row/cell-level security, LF-Tags for tag-based access control (TBAC), cross-account sharing. Replaces raw S3 IAM policies with database/table-level grants. (Conceptually = Unity Catalog for the AWS-native stack.)
- **Open table formats:** Iceberg, Hudi, Delta — ACID on S3, time travel, schema evolution. Athena/Glue natively support Iceberg; Glue 4.0+ supports all three.

### Security & Compliance
- **Macie:** ML-based discovery of sensitive data (PII, credentials, financial data) **in S3 specifically**. Produces findings → EventBridge → remediation. MCQ trigger word: "automatically discover PII in S3" → Macie.
- **CUI handling:** Encryption in transit (TLS) and at rest (KMS, ideally customer-managed keys), least-privilege IAM, VPC endpoints so data never traverses public internet, CloudTrail (+ S3 data events) for audit trails, GovCloud/FedRAMP boundaries, tagging + Lake Formation for access scoping, NIST 800-171 as the CUI control baseline.
- **Audit trail stack:** CloudTrail (API calls), CloudWatch Logs, AWS Config (resource state history), Lake Formation/Athena query logs.
- **KMS:** Envelope encryption, key policies vs IAM, cross-account grants, automatic rotation for CMKs.

### AI/ML Dataset Services
- **SageMaker:** Feature Store (online + offline stores), Data Wrangler (visual prep), Processing Jobs (run your own transform containers), Ground Truth (labeling), Pipelines (ML orchestration). Training data typically Parquet/RecordIO in S3.
- **Bedrock:** Managed foundation models via API. **Knowledge Bases** = managed RAG — you point it at S3 documents, it chunks, embeds (Titan or other embedding models), and stores in a vector store (OpenSearch Serverless, Aurora pgvector, Pinecone). Data engineer's job: curate, clean, chunk-appropriately-structure, and secure the S3 corpus; fine-tuning data goes in as JSONL.
- **Data-for-ML talking points:** deduplication, PII scrubbing before training (Macie + Glue jobs), train/test lineage, feature freshness, embedding refresh pipelines.

### Orchestration & IaC
- **Step Functions** (serverless state machines) vs **MWAA** (managed Airflow — you know this cold) vs **Glue Workflows** (Glue-only, simple).
- **Terraform:** `plan`/`apply`, remote state (S3 backend + DynamoDB locking), modules, `for_each`, workspaces. Key resources: `aws_glue_job`, `aws_glue_crawler`, `aws_s3_bucket`, `aws_lakeformation_permissions`.

---

## Part 3: Coding Question Prep

### Likely format
Timed, in-browser editor. Read the whole prompt first; they often hide edge-case requirements (nulls, duplicates, malformed rows) in the description. State assumptions in comments — assessors credit reasoning.

### Pattern 1: PySpark transformation (Glue-style)

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.window import Window

args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Read from catalog (DynamicFrame) then convert for full DataFrame API
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="bronze", table_name="orders"
)
df = dyf.toDF()

# Typical asked-for transforms: dedupe, cleanse, standardize, aggregate
cleaned = (
    df.dropDuplicates(["order_id"])
      .filter(F.col("order_total").isNotNull() & (F.col("order_total") > 0))
      .withColumn("order_date", F.to_date("order_ts"))
      .withColumn("email", F.lower(F.trim("email")))
)

# Latest record per key — the single most common senior-level pattern
w = Window.partitionBy("customer_id").orderBy(F.col("updated_at").desc())
latest = cleaned.withColumn("rn", F.row_number().over(w)).filter("rn = 1").drop("rn")

# Write partitioned Parquet
(latest.write.mode("overwrite")
       .partitionBy("order_date")
       .parquet("s3://curated-bucket/orders/"))

job.commit()
```

Know cold: `row_number`/`rank`/`dense_rank` differences, `when/otherwise`, joins + broadcast hints (`F.broadcast(dim_df)`), `explode`, `coalesce` vs `repartition`, handling skew (salting keys).

### Pattern 2: SQL (Athena/ANSI)

Window functions are the senior-level filter. Drill these:

```sql
-- Dedupe to latest record per key
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY customer_id ORDER BY updated_at DESC) AS rn
  FROM customers_raw
) WHERE rn = 1;

-- Running total & moving average
SELECT order_date,
       SUM(amount) OVER (ORDER BY order_date) AS running_total,
       AVG(amount) OVER (ORDER BY order_date
         ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d
FROM daily_sales;

-- Gaps & islands / sessionization (LAG)
SELECT user_id, event_ts,
       CASE WHEN event_ts - LAG(event_ts) OVER (
         PARTITION BY user_id ORDER BY event_ts) > INTERVAL '30' MINUTE
       THEN 1 ELSE 0 END AS new_session_flag
FROM events;

-- Top-N per group
SELECT * FROM (
  SELECT region, product, revenue,
         DENSE_RANK() OVER (PARTITION BY region ORDER BY revenue DESC) AS rk
  FROM sales
) WHERE rk <= 3;
```

Also review: `QUALIFY` isn't in Athena (use subquery), `UNNEST` for arrays, CTEs, anti-joins (`LEFT JOIN ... WHERE right.id IS NULL` or `NOT EXISTS`), `date_trunc`, `try_cast` for dirty data.

### Pattern 3: Python API ingestion + cleansing

```python
import requests, time, json, boto3
from datetime import datetime, timezone

def fetch_all(base_url: str, api_key: str) -> list[dict]:
    """Paginated fetch with retry/backoff — say 'idempotent, resumable' out loud."""
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    results, page = [], 1
    while True:
        for attempt in range(3):
            try:
                r = session.get(base_url, params={"page": page, "per_page": 100}, timeout=30)
                if r.status_code == 429:  # rate limited
                    time.sleep(int(r.headers.get("Retry-After", 2 ** attempt)))
                    continue
                r.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        batch = r.json().get("results", [])
        if not batch:
            return results
        results.extend(batch)
        page += 1

def clean(records: list[dict]) -> list[dict]:
    seen, out = set(), []
    for rec in records:
        rid = rec.get("id")
        if rid is None or rid in seen:
            continue
        seen.add(rid)
        out.append({
            "id": rid,
            "email": (rec.get("email") or "").strip().lower() or None,
            "amount": float(rec["amount"]) if rec.get("amount") not in (None, "") else None,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })
    return out

def land_to_s3(records: list[dict], bucket: str, prefix: str):
    """Write NDJSON to a date-partitioned raw zone."""
    key = f"{prefix}/dt={datetime.now(timezone.utc):%Y-%m-%d}/batch_{int(time.time())}.jsonl"
    body = "\n".join(json.dumps(r) for r in records)
    boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=body.encode())
```

Talking points to embed in comments: pagination, exponential backoff + jitter, 429 handling, idempotency, dedupe, null normalization, typed casting, partitioned raw landing zone, never logging secrets.

### Pattern 4: pandas quick reference (in case it's pandas, not Spark)
`drop_duplicates(subset=..., keep="last")`, `pd.to_datetime(errors="coerce")`, `groupby().agg()`, `merge(how="left", indicator=True)`, `fillna`, `astype`, `pd.json_normalize` for nested API payloads, `melt`/`pivot_table`.

---

## Part 4: Long-Form Response Prep

### Framework: the 7-layer pipeline design answer
When asked "design a scalable AWS data pipeline for X," walk this structure every time:

1. **Requirements & constraints** — volume/velocity/variety, latency (batch vs streaming), SLAs, sensitivity level (CUI/PII → GovCloud, encryption, access controls). Asking clarifying assumptions up front reads as senior.
2. **Ingestion** — batch: AppFlow/DMS/Glue JDBC/API pulls via Lambda or Glue Python shell; streaming: Kinesis/MSK → Firehose to S3.
3. **Storage & layout** — S3 data lake with zone/medallion layering (raw → cleansed/silver → curated/gold), Parquet + Snappy, Hive-style partitioning aligned to query patterns, Iceberg/Delta for ACID + schema evolution.
4. **Processing** — Glue Spark jobs (or EMR for heavy/custom workloads), job bookmarks for incremental loads, Glue Data Quality rules gating promotion between zones.
5. **Orchestration** — MWAA/Airflow (your home turf) or Step Functions; event-driven triggers via S3 → EventBridge.
6. **Serving** — Athena for ad-hoc SQL, Redshift for BI concurrency, SageMaker/Bedrock for ML consumers, QuickSight dashboards.
7. **Cross-cutting** — governance (Glue Catalog + Lake Formation grants, LF-Tags), security (KMS CMKs, VPC endpoints, IAM least privilege, Macie scans on raw zone), observability (CloudWatch metrics/alarms, CloudTrail audit, data lineage), cost (partition pruning, lifecycle policies, workgroup scan limits), IaC (Terraform for every resource).

Close with tradeoffs you considered ("I chose Firehose over Streams because no custom consumers were needed, trading per-record latency for zero shard management"). Explicit tradeoffs are the #1 senior signal.

### Likely long-form prompts & how you'd anchor them in your experience

**"Describe a data pipeline you built and how you optimized it."**
Use the NASA EDP medallion pipelines (PRACA/FMEA/LCC/Flight Hazards): XML parser migration into Databricks, bronze→silver→gold promotion, Liquid Clustering for layout optimization, Airflow orchestration, Unity Catalog governance. Translate vocabulary: Unity Catalog ↔ Glue Catalog + Lake Formation; Auto Loader/checkpoints ↔ job bookmarks; Liquid Clustering ↔ partitioning/bucketing strategy. Explicitly say the concepts transfer — that turns your Databricks depth into an asset instead of a gap.

**"How do you ensure data quality?"**
Structure: (1) validation at ingestion (schema enforcement, typed casts, quarantine/dead-letter path for bad records), (2) rule-based checks between zones (Glue Data Quality/Deequ or Great Expectations: completeness, uniqueness, referential integrity, freshness), (3) reconciliation against source counts, (4) monitoring & alerting on DQ metrics, (5) fail-closed promotion — bad data never reaches gold. Cite your bronze-to-silver USASpending cleaning work (310+ columns) as concrete scale.

**"How do you handle CUI/PII securely?"**
This is where your GovCloud/FedRAMP High background is a differentiator most candidates can't match. Cover: GovCloud boundary & FedRAMP High baseline, NIST 800-171 for CUI, KMS CMKs with key policies, TLS everywhere, VPC endpoints (no public internet path), IAM least privilege + Lake Formation column/row-level grants, Macie automated PII discovery feeding EventBridge remediation, CloudTrail + S3 data events for audit trails, tokenization/masking in non-prod, tagging for data classification. Mention your GuardDuty centralization architecture (EventBridge + Lambda + S3 across accounts) as proof you've built security plumbing, not just consumed it.

**"How do you prepare datasets for AI/ML?"**
Cover: curated gold-zone feature datasets, SageMaker Feature Store for online/offline consistency, deduplication + PII scrubbing before training, train/val/test splits with lineage, drift monitoring, and for Bedrock: document curation → chunking strategy → embeddings → Knowledge Base/vector store, with access controls carried through to retrieval. Your Intervals AI Coach RAG/agent work and MCP server building gives you genuinely current talking points on LLM data pipelines and AI-assisted development (a listed nice-to-have).

**"Tell us about performance tuning."**
Spark: partition sizing (~128 MB–1 GB files, avoid small-file problem — compaction jobs), broadcast joins for small dims, salting skewed keys, caching only when reused, right-sizing DPUs/workers, predicate pushdown. SQL/warehouse: partition pruning, columnar formats, sort/distribution keys in Redshift, stats collection. Athena: everything in the Athena section above. Storage: lifecycle policies, Intelligent-Tiering.

### Long-form writing tips
- Lead with a one-sentence architecture summary, then structure with the 7 layers.
- Quantify wherever possible (data volumes, latency targets, cost reductions, column counts).
- Name specific services and *why chosen over alternatives*.
- End with monitoring/operations — pipelines that run themselves are the senior signature.

---

## Part 5: Databricks → AWS-Native Translation Table (your personal gap-closer)

| You know (Databricks/EDP) | Assessment vocabulary (AWS-native) |
|---|---|
| Unity Catalog | Glue Data Catalog + Lake Formation |
| Delta Lake ACID tables | Iceberg/Hudi/Delta on S3 (Athena favors Iceberg) |
| Auto Loader / streaming checkpoints | Glue job bookmarks / Kinesis + Firehose |
| Liquid Clustering / OPTIMIZE / Z-ORDER | S3 partitioning + bucketing + compaction jobs |
| Databricks Jobs / Workflows | Glue Workflows / Step Functions / MWAA |
| Medallion (bronze/silver/gold) | Lake zones (raw/cleansed/curated) — same idea, say both names |
| Genie Spaces / DBSQL | Athena + QuickSight |
| Databricks SQL warehouse | Redshift / Athena |
| Photon | Nothing to translate — just don't mention it |
| DBFS | S3 direct (DBFS is deprecated anyway — you documented this) |
| Databricks secrets | Secrets Manager / SSM Parameter Store |

## Part 6: Two-Day Cram Plan

**Day 1 (concepts):** Part 2 rapid-fire facts (90 min) → Athena optimization + Kinesis-vs-Firehose-vs-MSK decision rules (45 min) → security/CUI section, rehearse your GovCloud story out loud (45 min) → skim Lake Formation + Macie docs pages (30 min).

**Day 2 (hands-on):** Write the three SQL window-function patterns from memory (45 min) → write the PySpark dedupe-latest-record pattern from memory (45 min) → write the API ingestion function from memory (30 min) → outline answers to all five long-form prompts in Part 4, 5 bullets each (60 min) → speed-review the translation table right before the assessment.

Good luck — your FedRAMP/GovCloud + Databricks + agentic AI combination is rarer than anything on their must-have list. The assessment is mostly about proving the AWS-native vocabulary maps onto what you already do daily.
