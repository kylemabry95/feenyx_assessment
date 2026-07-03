# Senior Data Engineer — Detailed Study Guide

This folder breaks the one-page [senior-data-engineer-study-guide.md](../senior-data-engineer-study-guide.md) into deeper, **beginner-friendly** chapters. If you're not a data engineer yet, start at the top and go in order. If you already know the basics, jump to whatever subject you're weak on.

Every chapter follows the same shape:

- **In plain English** — the idea explained with no jargon.
- **Why it exists** — the problem it solves.
- **How it actually works** — the mechanics you need to understand.
- **Key facts to memorize** — the exam/interview-ready bullets.
- **Common gotchas** — the traps beginners fall into.
- **Check yourself** — quick questions to test recall.

## Reading order

| # | Chapter | What you'll learn |
|---|---------|-------------------|
| 00 | [Data Engineering Fundamentals](00-data-engineering-fundamentals.md) | The vocabulary everything else assumes: ETL, data lakes, partitioning, file formats, batch vs streaming |
| 01 | [Amazon S3 — Storage](03-amazon-s3.md) | The foundation of a data lake: object storage, prefixes, storage classes |
| 02 | [AWS Glue — ETL](01-aws-glue.md) | Serverless Spark ETL, the Data Catalog, crawlers, jobs, bookmarks |
| 03 | [Amazon Athena — Querying](02-amazon-athena.md) | Serverless SQL over S3 and how to make it cheap and fast |
| 04 | [Streaming — Kinesis & Kafka](04-streaming.md) | Real-time data: Kinesis Data Streams, Firehose, MSK |
| 05 | [Warehouses & Lakes](05-warehousing-and-lakes.md) | Redshift, Lake Formation, and open table formats (Iceberg/Hudi/Delta) |
| 06 | [Security & Compliance](06-security-and-compliance.md) | Encryption, IAM, Macie, CUI/PII handling, audit trails |
| 07 | [AI/ML Data Services](07-ai-ml-data-services.md) | SageMaker, Bedrock, and preparing data for machine learning |
| 08 | [Orchestration & IaC](08-orchestration-and-iac.md) | Airflow/MWAA, Step Functions, Glue Workflows, Terraform |
| 09 | [PySpark for Data Engineers](09-pyspark.md) | Distributed data processing, the patterns you'll be asked to code |
| 10 | [SQL & Window Functions](10-sql-window-functions.md) | The senior-level SQL patterns that show up in every assessment |
| 11 | [Python API Ingestion](11-python-api-ingestion.md) | Pulling data from APIs reliably: pagination, retries, idempotency |
| 12 | [Pipeline Design & Architecture](12-pipeline-design.md) | The 7-layer framework for designing a data platform end-to-end |
| 13 | [Data Quality](13-data-quality.md) | How to make sure your data is trustworthy |

## How to use this for the assessment

The original guide's **Two-Day Cram Plan** (Part 6) still applies. These chapters are the "explain it to me like I'm new" backing material for each rapid-fire fact. Read the chapter once for understanding, then use the original one-pager for last-minute review.
