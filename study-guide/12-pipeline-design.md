# 12 — Pipeline Design & Architecture

Prereqs: ideally all prior chapters — this is where they come together. The **long-form responses** are where the assessment is won, and they're almost always "design a data pipeline/platform for X." This chapter gives you a repeatable structure so you never freeze.

---

## The mindset

A senior answer isn't a list of services — it's a **reasoned design with explicit tradeoffs.** Interviewers want to see that you (1) clarify requirements first, (2) cover the whole lifecycle, and (3) justify each choice against alternatives. The structure below guarantees you cover everything.

---

## The 7-layer framework (walk this every time)

When asked "design a scalable AWS data pipeline for X," go through these seven layers in order. Even a rough pass across all seven beats a deep dive on one.

### 1. Requirements & constraints
Start by **asking clarifying questions** — this alone reads as senior. Nail down:
- **Volume / velocity / variety** — how much data, how fast, what formats?
- **Latency** — batch (hourly/daily) or streaming (seconds)? Don't build streaming if batch suffices.
- **SLAs** — how fresh must data be, how reliable?
- **Sensitivity** — CUI/PII? → GovCloud, encryption, fine-grained access from the start.

### 2. Ingestion
How data enters:
- **Batch:** AppFlow (SaaS), DMS (database migration/CDC), Glue JDBC connections, or API pulls via Lambda / Glue Python Shell.
- **Streaming:** Kinesis Data Streams / MSK → Firehose to S3.

### 3. Storage & layout
- **S3 data lake** with **zone/medallion layering** (raw → cleansed/silver → curated/gold).
- **Parquet + Snappy** columnar storage.
- **Hive-style partitioning** aligned to query patterns (usually by date).
- **Iceberg/Delta** table format for ACID + schema evolution where you need updates/time travel.

### 4. Processing
- **Glue Spark jobs** for transformation (or **EMR** for heavy/custom workloads).
- **Job bookmarks** for incremental loads.
- **Glue Data Quality** rules gating promotion between zones (bad data doesn't move up).

### 5. Orchestration
- **MWAA/Airflow** (complex, your strength) or **Step Functions** (serverless).
- **Event-driven** triggers via **S3 → EventBridge** so pipelines start on data arrival.

### 6. Serving
Match the consumer to the tool:
- **Athena** — ad-hoc SQL.
- **Redshift** — high-concurrency BI.
- **SageMaker / Bedrock** — ML/AI consumers.
- **QuickSight** — dashboards.

### 7. Cross-cutting concerns (the senior differentiator)
The stuff juniors forget:
- **Governance** — Glue Catalog + Lake Formation grants, LF-Tags.
- **Security** — KMS CMKs, VPC endpoints, IAM least privilege, Macie scans on the raw zone.
- **Observability** — CloudWatch metrics/alarms, CloudTrail audit, data lineage.
- **Cost** — partition pruning, lifecycle policies, workgroup scan limits.
- **IaC** — Terraform for every resource.

---

## Close with tradeoffs (the #1 senior signal)

End every design by naming **choices you made and what you traded away**:

> "I chose **Firehose over Kinesis Data Streams** because there were no custom consumers — trading per-record latency for zero shard management."

> "I used **Iceberg** for the silver layer because we need row-level updates and time travel for audits, accepting slightly more write complexity than plain Parquet."

Explicit tradeoffs are what interviewers grade highest. Always give at least two.

---

## Writing tips for long-form answers

1. **Lead with a one-sentence architecture summary**, then expand through the 7 layers.
2. **Quantify** wherever possible — data volumes, latency targets, cost reductions, column counts. Numbers read as real experience.
3. **Name specific services *and why* over alternatives.**
4. **End with monitoring/operations** — "the pipeline runs itself and alerts on failure." Self-operating pipelines are the senior signature.

---

## The five likely prompts and how to anchor them

Ground answers in real experience — vague answers lose. These map to the original guide's Part 4.

### "Describe a data pipeline you built and how you optimized it."
Use the **NASA EDP medallion pipelines** (PRACA/FMEA/LCC/Flight Hazards): XML parser migration into Databricks, bronze→silver→gold promotion, Liquid Clustering for layout optimization, Airflow orchestration, Unity Catalog governance. **Translate the vocabulary** to AWS-native as you go (Unity Catalog ↔ Glue Catalog + Lake Formation; Auto Loader ↔ job bookmarks; Liquid Clustering ↔ partitioning/bucketing). Explicitly say the concepts transfer — that turns Databricks depth into an asset, not a gap.

### "How do you ensure data quality?"
See [chapter 13](13-data-quality.md). Structure: validation at ingestion → rule-based checks between zones → reconciliation vs source counts → monitoring/alerting → **fail-closed promotion**. Cite the **USASpending bronze→silver cleaning (310+ columns)** for concrete scale.

### "How do you handle CUI/PII securely?"
Your differentiator — see [chapter 06](06-security-and-compliance.md). GovCloud + FedRAMP High + NIST 800-171, KMS CMKs, TLS, VPC endpoints, IAM least privilege + Lake Formation grants, Macie → EventBridge remediation, CloudTrail + S3 data events, tokenization in non-prod. Mention the **GuardDuty centralization architecture** (EventBridge + Lambda + S3 cross-account) as proof you've *built* security plumbing.

### "How do you prepare datasets for AI/ML?"
See [chapter 07](07-ai-ml-data-services.md). Curated gold-zone features, SageMaker Feature Store, dedup + PII scrubbing before training, train/val/test with lineage, drift monitoring; for Bedrock: curate → chunk → embed → Knowledge Base/vector store with access controls through retrieval. Cite your **Intervals AI Coach RAG/agent + MCP** work as current LLM-pipeline experience.

### "Tell us about performance tuning."
- **Spark:** partition sizing (~128 MB–1 GB, fix small files with compaction), broadcast joins, salt skewed keys, cache only when reused, right-size DPUs, predicate pushdown.
- **SQL/warehouse:** partition pruning, columnar formats, Redshift sort/distribution keys, stats collection.
- **Athena:** Parquet + compression + partition-and-filter (see [chapter 02](02-amazon-athena.md)).
- **Storage:** lifecycle policies, Intelligent-Tiering.

---

## Key facts to memorize

- **7 layers:** Requirements → Ingestion → Storage/Layout → Processing → Orchestration → Serving → Cross-cutting.
- Always **clarify requirements first** and **end with explicit tradeoffs.**
- **Cross-cutting = governance, security, observability, cost, IaC** — the senior differentiator.
- Lead with a one-sentence summary, **quantify**, justify vs alternatives, close with **monitoring/ops**.

---

## Check yourself

1. List the 7 layers from memory.
2. What two things bracket every senior answer (start and finish)?
3. Give a tradeoff statement for choosing Firehose over Kinesis Data Streams.
4. Which cross-cutting concerns do juniors typically forget?
5. How would you translate "Unity Catalog" and "Auto Loader" into AWS-native terms mid-answer?
