# 04 — Streaming (Kinesis & Kafka/MSK)

Prereq: [00 — Fundamentals](00-data-engineering-fundamentals.md) (the batch-vs-streaming section). This chapter is about moving data **in real time**.

---

## In plain English

Batch pipelines process data in scheduled chunks. **Streaming pipelines process each record the moment it arrives** — a click, a payment, a sensor reading — continuously, forever. This chapter covers the AWS tools for capturing and moving those streams: **Kinesis Data Streams**, **Kinesis Data Firehose**, and **MSK (Managed Kafka)**.

The single most common exam question is: **which one do I pick?** So we'll build to a decision rule.

---

## Why streaming exists

Some questions can't wait for the nightly batch: fraud detection, live dashboards, real-time recommendations, IoT alerts. For these you need data to flow within seconds. Streaming systems are essentially **durable, ordered pipes** that let producers write records and consumers read them as they arrive.

---

## Kinesis Data Streams

**A managed, real-time data stream you read from with custom consumers.** Producers write records in; one or more consumer applications read them out and do whatever they want (transform, aggregate, trigger actions).

Key concept — the **shard**:

- A **shard** is the unit of throughput. Each shard handles **1 MB/sec or 1,000 records/sec IN**, and **2 MB/sec OUT**.
- Need more throughput? Add shards. This is manual capacity planning (or use **on-demand mode**, which auto-scales for you).
- Records with the same **partition key** go to the same shard, which **preserves ordering per key** (all events for `user_123` stay in order).

Other facts:

- **Retention:** 24 hours by default, extendable up to **365 days.** Within that window you can **replay** data (re-read from the past) — great for reprocessing.
- **Enhanced fan-out** gives each consumer its own dedicated **2 MB/sec** pipe (instead of sharing the shard's output), reducing latency when you have many consumers.

**Choose Kinesis Data Streams when you need:** custom consumer logic, the ability to replay, or strict ordering per key.

---

## Kinesis Data Firehose

**A fully managed delivery service that lands streaming data into storage with zero management.** You point Firehose at a destination and it just... delivers. No shards, no consumers to write.

- **Destinations:** S3, Redshift, OpenSearch, Splunk, and some third parties.
- **Near-real-time, not instant:** it **buffers** by size (e.g., 5 MB) or time (e.g., 60 seconds), then flushes a batch. So there's a small delay by design.
- **Inline transformation:** can invoke a **Lambda** to transform records on the way through, and can **convert JSON to Parquet** before writing to S3.
- **No shard management, no custom consumers** — that's the whole point.

**Choose Firehose when you need:** the simplest possible way to get streaming data into S3 (often as Parquet) without writing consumer code.

---

## MSK (Managed Streaming for Apache Kafka)

**AWS-managed Apache Kafka.** Kafka is the open-source industry-standard streaming platform. MSK runs the Kafka brokers for you but keeps full Kafka API compatibility.

**Choose MSK when you need:**

- **Kafka API compatibility** — you have existing Kafka producers/consumers, Kafka Connect, or tooling.
- **Longer retention** or very high throughput.
- **Exactly-once semantics** and the rich Kafka ecosystem.

Trade-off: **more operational burden** than Kinesis even though it's "managed" — you still think about brokers, partitions, topics, and tuning.

---

## The decision rule (memorize this)

| Requirement | Pick |
|---|---|
| "Simplest way to land streaming data in S3 as Parquet" | **Firehose** |
| "Custom consumers / replay / ordering per key" | **Kinesis Data Streams** |
| "We need Kafka APIs / existing Kafka tooling" | **MSK** |

A very common architecture combines them: **Kinesis Data Streams (ingest + custom processing) → Firehose (delivery to S3)**. Or simply **source → Firehose → S3 as Parquet** when no custom processing is needed.

---

## Key facts to memorize

- **Kinesis Data Streams:** shard = 1 MB/s or 1,000 rec/s in, 2 MB/s out. Retention 24h default → 365 days. On-demand auto-scales. Enhanced fan-out = dedicated 2 MB/s per consumer. Partition key preserves ordering. Supports replay + custom consumers.
- **Firehose:** fully managed *delivery* to S3/Redshift/OpenSearch/Splunk. Buffers by size/time (near-real-time). Lambda transform + JSON→Parquet conversion. No shards, no consumers.
- **MSK:** managed Kafka; pick for Kafka compatibility, long retention, exactly-once, existing tooling. Most ops burden.

---

## Common gotchas

- **Firehose is not instant** — it buffers. If someone asks for sub-second latency, Firehose alone won't do it.
- **Shard limits are real** — a hot partition key can overload one shard while others idle (streaming's version of data skew). Choose partition keys with good distribution.
- Don't reach for MSK just because you've "heard of Kafka" — if you don't need Kafka APIs, Kinesis is less work.
- Streaming data still needs the **small-files** and **compaction** treatment once it lands in S3.

---

## Databricks translation

| Databricks | AWS-native |
|---|---|
| Structured Streaming from Kafka | Kinesis Data Streams / MSK consumers |
| Auto Loader landing streamed files | Firehose → S3 |

---

## Check yourself

1. What is a shard and what are its throughput limits?
2. Why is Firehose "near-real-time" rather than instant?
3. Give the one-line decision rule for Streams vs Firehose vs MSK.
4. How does Kinesis preserve ordering, and what can go wrong with a bad partition key?
5. When is MSK worth its extra operational cost?
