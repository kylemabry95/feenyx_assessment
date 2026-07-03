# 07 — AI/ML Data Services (SageMaker & Bedrock)

Prereqs: [00 — Fundamentals](00-data-engineering-fundamentals.md), [03 — S3](03-amazon-s3.md), [06 — Security](06-security-and-compliance.md).

Your job as a data engineer isn't to build the models — it's to **prepare, serve, and secure the data the models consume.** This chapter covers the two AWS services you'll be asked about (SageMaker for traditional ML, Bedrock for generative AI/LLMs) and, more importantly, the **data-engineering responsibilities** around them.

---

## The mental model

Machine learning is only as good as its data. A model that trains on duplicated, biased, or PII-leaking data produces garbage or legal risk. So the data engineer owns:

- **Curation** — assembling clean, relevant datasets.
- **Deduplication** — the same record twice skews the model.
- **PII scrubbing** — remove/mask sensitive data *before* training (Macie + Glue jobs).
- **Lineage** — track which data produced which model (for audits and reproducibility).
- **Freshness** — keep features and embeddings up to date.

---

## Amazon SageMaker — traditional ML platform

SageMaker is AWS's end-to-end platform for building, training, and deploying ML models. The pieces a **data engineer** cares about:

- **Feature Store** — a central repository for **features** (the input variables a model uses). It has:
  - an **offline store** (in S3) for training on historical data, and
  - an **online store** for low-latency lookups at prediction time.
  - The key value: **consistency** — the same feature definition serves both training and real-time inference, avoiding "training/serving skew."
- **Data Wrangler** — a **visual data-prep tool** for cleaning and transforming ML datasets.
- **Processing Jobs** — run *your own* transformation code in containers at scale (e.g., a big preprocessing step).
- **Ground Truth** — a **data-labeling** service (humans/ML label training data).
- **Pipelines** — orchestration specifically for **ML workflows** (prep → train → evaluate → deploy).

Training data is typically **Parquet or RecordIO** files in **S3.**

---

## Amazon Bedrock — generative AI / LLMs

**Bedrock gives you access to foundation models (LLMs like Claude, Titan, etc.) through a single API**, without managing any model infrastructure. The data-engineering-relevant feature is **Knowledge Bases**.

### Knowledge Bases = managed RAG

**RAG (Retrieval-Augmented Generation)** means: instead of relying only on what the LLM memorized, you **retrieve relevant documents from your own data and feed them to the model** so it answers from *your* content. It's how you make an LLM answer questions about your company's documents.

Bedrock Knowledge Bases automate the RAG pipeline:

1. You point it at **S3 documents.**
2. It **chunks** them (splits long docs into passages).
3. It **embeds** each chunk — converts text into a vector (a list of numbers capturing meaning) using an **embedding model** (Titan or others).
4. It stores those vectors in a **vector store** — **OpenSearch Serverless, Aurora pgvector, or Pinecone.**
5. At query time it finds the chunks most similar to the question and hands them to the LLM.

**The data engineer's job here:** curate, clean, and **structure/chunk the S3 corpus appropriately**, keep it fresh, and carry **access controls through to retrieval** (a user shouldn't retrieve a document they're not allowed to see). **Fine-tuning data** goes in as **JSONL.**

---

## Data-for-ML talking points (say these in long-form answers)

- **Deduplication** and **PII scrubbing before training** (Macie + Glue).
- **Train/validation/test splits** with **lineage** so results are reproducible.
- **Feature freshness** and **embedding refresh pipelines** (re-embed when source docs change).
- **Drift monitoring** — watch for the input data distribution changing over time, which degrades models.
- **Access controls carried through to retrieval** in RAG — security doesn't stop at storage.

---

## Key facts to memorize

- **SageMaker Feature Store:** online + offline stores; ensures training/serving consistency.
- SageMaker also has **Data Wrangler** (visual prep), **Processing Jobs** (your containers), **Ground Truth** (labeling), **Pipelines** (ML orchestration). Training data = **Parquet/RecordIO in S3.**
- **Bedrock** = foundation models via API. **Knowledge Bases = managed RAG**: S3 docs → chunk → embed (Titan) → vector store (OpenSearch Serverless / Aurora pgvector / Pinecone).
- **Fine-tuning data = JSONL.**
- Data engineer owns: curation, dedup, **PII scrubbing before training**, chunking strategy, freshness, lineage, and access control through retrieval.

---

## Common gotchas

- **Chunking matters** — chunks too big dilute relevance; too small lose context. This is a real tuning decision, not an afterthought.
- **PII must be scrubbed *before* training/embedding**, not after — once it's in the model or vector store it's hard to remove.
- **RAG security** — remember to enforce access controls at *retrieval* time, not just storage.
- Don't confuse **embeddings** (vectors for retrieval) with **fine-tuning** (actually adjusting model weights). RAG uses embeddings; JSONL is for fine-tuning.

---

## Your differentiator

Your Intervals AI Coach RAG/agent work and MCP-server building give you **current, hands-on** LLM-pipeline talking points — chunking strategies, embedding refresh, agentic tool use — which is a listed nice-to-have most candidates can't speak to authentically.

---

## Check yourself

1. Why does the SageMaker Feature Store have both an online and offline store?
2. Explain RAG in one sentence.
3. Walk through what a Bedrock Knowledge Base does to an S3 document, step by step.
4. Where does PII scrubbing belong in an ML data pipeline, and why there?
5. What's the difference between using embeddings (RAG) and fine-tuning?
