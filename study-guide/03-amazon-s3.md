# 03 — Amazon S3 (Storage)

Prereq: [00 — Fundamentals](00-data-engineering-fundamentals.md). S3 is the foundation of almost every AWS data pipeline, so learn it before Glue and Athena.

---

## In plain English

**S3 (Simple Storage Service) is an infinitely large hard drive in the cloud that you access over the internet.** You put files in, you get files out, and AWS handles all the disks, backups, and durability. It's cheap, it never runs out of space, and nearly every other AWS data service reads from and writes to it.

In data engineering, **S3 *is* your data lake.** All your raw, cleansed, and curated data lives here as files.

---

## Why it exists

Running your own storage servers is painful: disks fail, you run out of space, you have to back things up. S3 makes storage a service — you never think about hardware. AWS promises **eleven 9s of durability** (99.999999999%), meaning if you store 10 million files, you'd expect to lose one every 10,000 years. That reliability is why it's the trusted home for a data lake.

---

## How it actually works

### Buckets and objects

- A **bucket** is a top-level container with a globally unique name (e.g., `nasa-edp-raw-zone`). Think of it as the root folder.
- An **object** is a single file plus its metadata. Each object has a **key** (its full path, like `orders/year=2026/month=07/file.parquet`).

**Important mental model: S3 has no real folders.** It's a flat key-value store. The "folders" you see are just a UI trick based on the `/` characters in keys. This matters for the next point.

### Prefixes

A **prefix** is the leading part of a key — everything up to the last `/`. In `orders/year=2026/month=07/file.parquet`, the prefix is `orders/year=2026/month=07/`.

Prefixes matter for **performance and partitioning**:

- S3 scales throughput **per prefix**: **3,500 PUT/POST/DELETE and 5,500 GET requests per second, per prefix.** If you need more throughput, spread data across more prefixes so requests parallelize.
- Partitioning your data lake by date (`year=/month=/day=`) creates many prefixes — which is exactly how Athena and Glue prune to only the data they need.

### Consistency

Since December 2020, S3 provides **strong read-after-write consistency** for all operations. Translation: the instant you write an object, any read will see the latest version. You used to have to worry about "eventual consistency" (a read might return stale data briefly) — that's gone now. If you see an old exam question mentioning eventual consistency, it's outdated.

---

## Storage classes (cost tiers)

You pay less if you tell S3 how often you'll access data. From most-accessed/most-expensive to archival/cheapest:

| Class | Use for | Notes |
|---|---|---|
| **Standard** | Hot data, frequent access | Default, most expensive per GB |
| **Intelligent-Tiering** | You don't know the access pattern | **Auto-moves data between tiers, no retrieval fees.** Safe default |
| **Standard-IA** (Infrequent Access) | Accessed monthly-ish | Cheaper storage, but you pay a retrieval fee |
| **One Zone-IA** | Re-creatable data | Cheaper still, but stored in one AZ (less durable) |
| **Glacier Instant Retrieval** | Archive, need it in ms | |
| **Glacier Flexible Retrieval** | Archive, minutes-to-hours ok | |
| **Glacier Deep Archive** | Compliance archive, 12h ok | Cheapest possible |

> **Exam trigger:** "automatically optimize storage cost without knowing access patterns" → **Intelligent-Tiering** (the key selling point is *no retrieval fees* and automatic movement).

### Lifecycle policies

Rules that **automatically move or delete objects as they age.** E.g., "move to Standard-IA after 30 days, Glacier after 90, delete after 7 years." They can also **abort incomplete multipart uploads** (leftover junk from failed big-file uploads that silently costs money). Lifecycle policies are the main cost-control lever for a data lake.

---

## Security (a big topic for this role)

Because a data lake holds sensitive data, S3 security shows up everywhere — especially for CUI/PII work.

- **Block Public Access** — a master switch that prevents a bucket from being exposed to the internet. Turn it **on** for data lakes. Misconfigured public buckets are the #1 cause of cloud data leaks.
- **Bucket policies** — resource-based JSON rules on the bucket ("this account/role may read, no one else"). Contrast with IAM policies, which are attached to users/roles.
- **Encryption at rest** — three options:
  - **SSE-S3** — AWS manages the keys. Simplest.
  - **SSE-KMS** — keys managed in AWS KMS; you get access control and an audit trail on key usage. **This is what you want for CUI/PII** (ideally customer-managed keys, CMKs).
  - **SSE-C** — you supply and manage the keys yourself. Rare.
- **Encryption in transit** — enforce TLS (HTTPS) so data is encrypted while moving.
- **VPC endpoints** — let your AWS resources reach S3 over Amazon's private network instead of the public internet. **Gateway endpoints for S3 are free.** Critical for compliance ("data never traverses the public internet").
- **Object Lock** — WORM (Write Once, Read Many) storage for compliance. Once locked, an object can't be deleted or changed for a set retention period. Used for audit logs and regulatory records.

---

## Event notifications — the trigger backbone

S3 can **emit an event whenever an object is created/deleted**, and send it to:

- **Lambda** — run code immediately (e.g., validate/transform the new file).
- **SQS** — queue it for reliable processing.
- **SNS** — fan out to multiple subscribers.
- **EventBridge** — route it with rich filtering rules.

This is what makes pipelines **event-driven**: instead of polling "is there new data yet?", a new file *automatically* kicks off the next step. Remember this — it's how modern serverless pipelines start.

---

## Key facts to memorize

- S3 = object storage, ~infinite, **11 nines of durability**, the home of your data lake.
- No real folders — flat keys with prefixes. Scaling is **per prefix**: 3,500 write / 5,500 read requests per second.
- **Strong read-after-write consistency** on everything (since Dec 2020).
- **Intelligent-Tiering** = automatic cost optimization, no retrieval fees.
- **Lifecycle policies** transition/expire data and clean up failed multipart uploads.
- Security stack: Block Public Access, bucket policies, **SSE-KMS with CMKs** for sensitive data, TLS in transit, **free S3 gateway VPC endpoints**, Object Lock for WORM.
- S3 events → Lambda/SQS/SNS/EventBridge = the trigger backbone of event-driven pipelines.

---

## Common gotchas

- **`LIMIT` in a query doesn't reduce S3 scan cost** — only partitioning and columnar formats do (more in the Athena chapter). People assume `LIMIT 10` is cheap; it isn't if the engine still scans the whole file.
- **Small files problem** lives here too: millions of tiny objects hurt performance and rack up per-request costs. Compact them.
- **Public bucket = breach.** Always confirm Block Public Access is on for data lakes.
- Storage class transitions have minimums (e.g., you're billed a minimum duration in IA/Glacier) — don't ping-pong data between classes.

---

## Check yourself

1. Why does S3 have "no folders," and what's a prefix?
2. Which storage class do you pick when you don't know the access pattern, and why?
3. Which encryption option gives you an audit trail on key usage, and when would you require it?
4. How does an S3 event notification make a pipeline "event-driven"?
5. What's the per-prefix request-rate limit, and why does partitioning help?
