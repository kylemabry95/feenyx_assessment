# 09 — PySpark for Data Engineers

Prereqs: [00 — Fundamentals](00-data-engineering-fundamentals.md), [01 — Glue](01-aws-glue.md). This is a **coding** chapter — you may be asked to write a PySpark transformation live.

---

## In plain English

**Spark is a tool for processing data that's too big for one computer, by splitting the work across many machines.** **PySpark** is Spark's Python interface. You write what *looks* like pandas code, but under the hood Spark distributes it across a cluster.

The key mental shift from pandas: **Spark is lazy and distributed.** Your data is split into partitions spread across worker machines, and Spark doesn't actually run anything until you ask for a result.

---

## Core concepts you must understand

### DataFrames

A Spark **DataFrame** is a distributed table (rows and named, typed columns). You transform it with method chains. It's conceptually like a pandas DataFrame but spread across many machines.

### Lazy evaluation: transformations vs actions

- **Transformations** (`filter`, `select`, `withColumn`, `join`, `groupBy`) are **lazy** — they just build up a plan; nothing runs yet.
- **Actions** (`show`, `count`, `collect`, `write`) **trigger execution** — now Spark optimizes the whole plan and runs it.

Why it matters: Spark can optimize the entire chain before executing (e.g., pushing filters down to read less data). It also means a chain of transformations is cheap until you call an action.

### Partitions and shuffles

- Data is divided into **partitions** processed in parallel.
- A **shuffle** is when data must move across the network between machines (needed for `groupBy`, `join`, `distinct`, repartition). **Shuffles are the expensive operation** — minimizing them is most of Spark performance tuning.

---

## The patterns you'll be asked to code

### 1. Clean & deduplicate

```python
from pyspark.sql import functions as F

cleaned = (
    df.dropDuplicates(["order_id"])                       # remove exact dup keys
      .filter(F.col("order_total").isNotNull() & (F.col("order_total") > 0))
      .withColumn("order_date", F.to_date("order_ts"))    # cast string → date
      .withColumn("email", F.lower(F.trim("email")))      # standardize
)
```

### 2. Latest record per key (THE signature senior pattern)

Deduplicate to keep only the most recent row per key. Uses a **window function**:

```python
from pyspark.sql.window import Window

w = Window.partitionBy("customer_id").orderBy(F.col("updated_at").desc())
latest = (
    df.withColumn("rn", F.row_number().over(w))
      .filter("rn = 1")
      .drop("rn")
)
```

- `partitionBy` = group the rows (like SQL `PARTITION BY`, unrelated to storage partitions).
- `orderBy(...desc())` = newest first.
- `row_number() == 1` = keep the top row per group.

**Know the ranking-function differences cold:**
- **`row_number()`** — unique 1,2,3,4 even on ties.
- **`rank()`** — ties share a rank, then it **skips** (1,2,2,4).
- **`dense_rank()`** — ties share a rank, **no gaps** (1,2,2,3).

### 3. Joins and broadcast

```python
# Broadcast a SMALL dimension table to avoid a shuffle on the big table
result = big_fact_df.join(F.broadcast(small_dim_df), on="product_id", how="left")
```

**Broadcast join:** when one table is small, Spark copies it to every worker so the big table doesn't have to be shuffled — a major speedup. Reach for `F.broadcast()` on small dimension tables.

Join types to know: `inner`, `left`, `right`, `outer`, `left_anti` (rows in left with no match — great for "what's missing"), `left_semi` (rows in left that *have* a match).

### 4. Conditionals and arrays

```python
df = df.withColumn("tier",
        F.when(F.col("spend") > 1000, "gold")
         .when(F.col("spend") > 100, "silver")
         .otherwise("bronze"))

df = df.withColumn("item", F.explode("items"))   # one row per array element
```

---

## Performance tuning (very likely a talking point)

- **File/partition sizing** — aim for **~128 MB–1 GB** files. Fix the **small-files problem** with compaction; avoid too few huge partitions (no parallelism).
- **Broadcast joins** for small dimensions (above).
- **Data skew** — when one key has vastly more rows, one worker gets overloaded while others idle. **Fix with salting:** add a random suffix to the hot key to spread it across workers, then aggregate back.
- **`cache()` / `persist()`** — only when you **reuse** a DataFrame multiple times; caching something used once wastes memory.
- **`coalesce()` vs `repartition()`:**
  - `repartition(n)` — reshuffle into `n` partitions (can increase or decrease; full shuffle).
  - `coalesce(n)` — **reduce** partitions **without a full shuffle** (cheaper; use before writing to avoid many small output files).
- **Predicate pushdown** — filter early so Spark reads less from source (automatic with Parquet + partition filters).
- **Right-size DPUs/workers** in Glue — more workers = faster but pricier.

---

## Writing output

```python
(latest.write
       .mode("overwrite")            # or "append"
       .partitionBy("order_date")    # storage partitioning for downstream pruning
       .parquet("s3://curated/orders/"))
```

Write **partitioned Parquet** so downstream Athena/Glue queries prune efficiently.

---

## Glue-specific boilerplate

In a Glue job you'll see setup like this (from the study guide) — read source via DynamicFrame, convert to DataFrame, transform, write, then **`job.commit()`**:

```python
dyf = glueContext.create_dynamic_frame.from_catalog(database="bronze", table_name="orders")
df = dyf.toDF()          # convert to DataFrame for the real work
# ... transformations ...
job.commit()             # advances job bookmarks — don't forget it
```

---

## Key facts to memorize

- Spark is **lazy** — transformations build a plan, **actions** (`show`/`count`/`write`) trigger it.
- **Shuffles** (join/groupBy/distinct) are the expensive operation; minimize them.
- **Latest-record-per-key** = `Window.partitionBy(key).orderBy(ts.desc())` + `row_number() == 1`.
- **`row_number` vs `rank` vs `dense_rank`** — unique / gaps-on-ties / no-gaps.
- **`F.broadcast(small_df)`** avoids shuffling the big table.
- **Skew → salting.** **`coalesce`** reduces partitions without a full shuffle. **`cache`** only when reused.
- Target **128 MB–1 GB** files; write **partitioned Parquet**; **`job.commit()`** in Glue.

---

## Common gotchas

- **pandas habits don't transfer** — no true row-by-row loops; think in column transformations.
- Calling **`collect()`** pulls all data to the driver — can crash on big data. Avoid on large sets.
- Forgetting a DataFrame is **immutable** — every transform returns a new one; reassign.
- Leaving everything as a **DynamicFrame** (slow) — convert to DataFrame for heavy work.

---

## Check yourself

1. What's the difference between a transformation and an action?
2. Write the latest-record-per-key pattern from memory.
3. Explain `row_number` vs `rank` vs `dense_rank`.
4. When and why would you use `F.broadcast`?
5. What is data skew and how does salting fix it?
6. `coalesce` vs `repartition` — which shuffles?
