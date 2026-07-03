# 11 — Python API Ingestion

Prereqs: [00 — Fundamentals](00-data-engineering-fundamentals.md), [03 — S3](03-amazon-s3.md). A **coding** chapter: pulling data from an external API and landing it cleanly in your data lake.

---

## In plain English

Lots of data lives behind **web APIs** — you make an HTTP request, you get back JSON. Your job is to pull **all** of it, **reliably** (networks fail, APIs rate-limit you), clean it, and write it to S3 in an organized way. The assessment loves this because it tests real-world robustness, not just happy-path code.

The three things graders look for: **pagination** (get *all* the data, not just page 1), **resilience** (retries/backoff/rate-limit handling), and **idempotency** (safe to re-run without duplicates).

---

## The concepts, one at a time

### Pagination

APIs return data in pages (e.g., 100 records at a time) so responses stay small. You must **loop until there's no more data.** Common styles:

- **Page number** — `?page=1`, `?page=2`, ... until an empty page.
- **Offset/limit** — `?offset=0&limit=100`, then `offset=100`, ...
- **Cursor/token** — the response includes a `next_cursor`; you pass it back until it's null. (Most robust for changing data.)

Missing pagination = you silently ingest only the first page. Graders check for this specifically.

### Rate limiting and HTTP 429

APIs cap how often you can call them. Exceed it and you get **HTTP 429 "Too Many Requests"**, often with a **`Retry-After`** header telling you how long to wait. You must **honor it** and slow down rather than hammering the API.

### Retries with exponential backoff (+ jitter)

Transient failures (timeouts, 5xx errors) happen. Don't give up on the first failure and don't retry instantly in a tight loop. **Exponential backoff:** wait 1s, then 2s, then 4s, then 8s between retries (`2 ** attempt`). Add **jitter** (a little randomness) so many clients don't retry in sync and stampede the server.

### Idempotency

If the job crashes halfway and reruns, it must not create duplicates or double-count. Techniques: **dedupe by a stable ID**, write to **deterministic S3 keys** (so a rerun overwrites rather than appends), and design so partial runs are safe to resume.

### Never log secrets

API keys/tokens must never be printed to logs. Load them from **Secrets Manager / SSM Parameter Store** or env vars, and keep them out of error messages.

---

## The reference implementation (understand every line)

```python
import requests, time, json, boto3
from datetime import datetime, timezone

def fetch_all(base_url: str, api_key: str) -> list[dict]:
    """Paginated fetch with retry/backoff. Idempotent, resumable."""
    session = requests.Session()                               # reuse the connection
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    results, page = [], 1
    while True:                                                # PAGINATION loop
        for attempt in range(3):                              # RETRY loop
            try:
                r = session.get(base_url,
                                params={"page": page, "per_page": 100},
                                timeout=30)                    # always set a timeout
                if r.status_code == 429:                       # RATE LIMIT
                    time.sleep(int(r.headers.get("Retry-After", 2 ** attempt)))
                    continue                                   # retry same page
                r.raise_for_status()                           # raise on 4xx/5xx
                break                                          # success → exit retry loop
            except requests.RequestException:
                if attempt == 2:                               # last attempt → give up
                    raise
                time.sleep(2 ** attempt)                       # EXPONENTIAL BACKOFF
        batch = r.json().get("results", [])
        if not batch:                                          # no more data → done
            return results
        results.extend(batch)
        page += 1

def clean(records: list[dict]) -> list[dict]:
    """Dedupe + normalize nulls + type-cast."""
    seen, out = set(), []
    for rec in records:
        rid = rec.get("id")
        if rid is None or rid in seen:                         # DEDUPE by stable id
            continue
        seen.add(rid)
        out.append({
            "id": rid,
            "email": (rec.get("email") or "").strip().lower() or None,   # normalize
            "amount": float(rec["amount"]) if rec.get("amount") not in (None, "") else None,
            "ingested_at": datetime.now(timezone.utc).isoformat(),       # lineage stamp
        })
    return out

def land_to_s3(records: list[dict], bucket: str, prefix: str):
    """Write NDJSON to a date-partitioned raw zone."""
    key = f"{prefix}/dt={datetime.now(timezone.utc):%Y-%m-%d}/batch_{int(time.time())}.jsonl"
    body = "\n".join(json.dumps(r) for r in records)
    boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=body.encode())
```

### Why each piece matters

- **`requests.Session()`** — reuses the TCP connection across calls (faster than new connections).
- **`timeout=30`** — without a timeout a hung request blocks forever. Always set one.
- **`raise_for_status()`** — turns 4xx/5xx into exceptions your retry logic can catch.
- **Landing as NDJSON** (`.jsonl`) into a **date-partitioned raw zone** (`dt=YYYY-MM-DD/`) — this is your **bronze/raw** layer; keep the untouched original, convert to Parquet downstream.
- **`ingested_at`** timestamp — cheap **lineage**: you know when each record arrived.

---

## Talking points to say out loud (in comments or interview)

Pagination · exponential backoff **+ jitter** · **429/Retry-After** handling · **idempotency** · dedupe · null normalization · typed casting · **partitioned raw landing zone** · **never log secrets** · resumable.

---

## pandas quick reference (in case it's pandas, not raw dicts)

For cleansing tabular/nested API data with pandas:

- **`pd.json_normalize(data)`** — flatten nested JSON into a flat table (very common for API payloads).
- **`df.drop_duplicates(subset=["id"], keep="last")`** — dedupe.
- **`pd.to_datetime(col, errors="coerce")`** — parse dates, bad values become `NaT` instead of crashing.
- **`df.astype({...})`** — type-cast columns.
- **`df.fillna(...)`** — handle nulls.
- **`df.merge(other, how="left", indicator=True)`** — join; `indicator` shows match source (handy for anti-joins).
- **`df.groupby(...).agg(...)`**, **`melt`/`pivot_table`** — reshape.

---

## Key facts to memorize

- The three graded concerns: **pagination**, **resilience** (retry/backoff + 429/Retry-After), **idempotency**.
- **Exponential backoff** = `2 ** attempt`, **+ jitter** to avoid stampedes.
- Always set a **timeout**; use **`raise_for_status()`**; reuse a **Session**.
- **Dedupe by stable id**, normalize nulls, cast types, stamp **`ingested_at`**.
- Land raw as **NDJSON in a date-partitioned raw zone**; convert to Parquet downstream.
- **Never log secrets**; pull them from Secrets Manager/SSM.
- **`pd.json_normalize`** flattens nested API JSON.

---

## Common gotchas

- **Only fetching page 1** — the most common mistake. Always loop.
- **No timeout** → hangs forever.
- **Retrying on 4xx** (except 429) — a 400/401/404 won't fix itself; only retry 429 and 5xx/transient errors.
- **Appending non-deterministically** so reruns duplicate data — dedupe and/or use deterministic keys.
- **Logging the API key** in an error trace.

---

## Check yourself

1. What are the three things graders look for in an API ingestion task?
2. What is exponential backoff, and why add jitter?
3. What does HTTP 429 mean and how should you respond?
4. Why land raw JSON before converting to Parquet?
5. Which HTTP errors are worth retrying, and which aren't?
