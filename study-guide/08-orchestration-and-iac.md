# 08 — Orchestration & Infrastructure as Code

Prereqs: [00 — Fundamentals](00-data-engineering-fundamentals.md) (orchestration + IaC sections), [01 — Glue](01-aws-glue.md).

Two topics that turn a pile of scripts into a real, reliable, reproducible platform: **orchestration** (running the steps in order) and **IaC** (defining the infrastructure in code).

---

## Part A — Orchestration

### Why it exists

A real pipeline is many steps with dependencies: land data → validate → clean → aggregate → publish. If step 2 fails, step 3 must not run. If a step fails transiently, retry it. Someone must be alerted on failure. Doing this with cron and hope falls apart fast. An **orchestrator** manages the **DAG** (the dependency graph), schedules runs, retries failures, tracks state, and alerts.

### The three AWS options (know when to use each)

**1. MWAA (Managed Workflows for Apache Airflow)** — *your home turf*

- Managed **Apache Airflow**, the industry-standard orchestrator.
- You define DAGs in **Python**, giving you maximum flexibility, a rich ecosystem of operators (connect to almost anything), backfills, and a great UI.
- Best for **complex, cross-service pipelines** and teams that already know Airflow.
- Trade-off: more moving parts and cost than the lighter options; it's a real running environment.

**2. Step Functions** — serverless state machines

- AWS-native **serverless** orchestration. You define a **state machine** (a JSON/visual flow of states: task, choice, parallel, wait, retry, catch).
- **Pay per state transition**, scales to zero, deep native integration with Lambda and other AWS services.
- Best when you want **serverless, event-driven** orchestration without managing an Airflow environment, especially Lambda-heavy workflows.

**3. Glue Workflows** — Glue-only, simplest

- Orchestrates **only Glue crawlers + jobs + triggers.**
- Best when your **entire pipeline is Glue** and you don't need anything fancy. No extra service to run.

### Decision rule

| Situation | Pick |
|---|---|
| Complex, multi-service pipeline; team knows Airflow; need backfills | **MWAA** |
| Serverless, event-driven, Lambda-centric, pay-per-use | **Step Functions** |
| Pipeline is entirely Glue jobs/crawlers | **Glue Workflows** |

### Event-driven triggering

Orchestration doesn't have to be schedule-based. Combine with **S3 events → EventBridge** so a pipeline **starts the moment new data lands** rather than waiting for a clock. This is the modern, responsive pattern (see [chapter 03](03-amazon-s3.md)).

---

## Part B — Infrastructure as Code (Terraform)

### Why it exists

Clicking around the AWS console to create buckets, jobs, and IAM roles is unrepeatable and error-prone. **IaC means you write your infrastructure as code**, review it like any code, version it in git, and apply it consistently across dev/test/prod. You can destroy and rebuild an entire environment from the code. **Terraform** is the dominant tool.

### Terraform core concepts

- **`terraform plan`** — shows you *exactly* what will change before anything happens (a dry run). Always run it first.
- **`terraform apply`** — makes the changes real.
- **State** — Terraform keeps a **state file** mapping your code to real AWS resources. This must be shared and locked so teammates don't clobber each other:
  - **Remote state** in an **S3 backend**, with **DynamoDB for state locking** (prevents two people applying at once). Memorize this pairing — it's the standard answer.
- **Modules** — reusable, parameterized bundles of resources (e.g., a "data-lake bucket" module you instantiate many times).
- **`for_each`** — create many similar resources from a map/set without copy-paste.
- **Workspaces** — manage multiple environments (dev/staging/prod) from one config.

### Key AWS resources you'd write

- `aws_s3_bucket` — lake buckets.
- `aws_glue_job`, `aws_glue_crawler` — ETL.
- `aws_lakeformation_permissions` — governance grants.
- (plus IAM roles, KMS keys, Kinesis streams, etc.)

> **Senior signal:** "every resource is defined in Terraform" — reproducible, reviewable, auditable infrastructure. Say it explicitly.

---

## Key facts to memorize

- **MWAA** = managed Airflow, Python DAGs, complex/flexible, your strength.
- **Step Functions** = serverless state machines, pay-per-transition, Lambda-centric.
- **Glue Workflows** = Glue-only, simplest orchestration.
- **Event-driven** start: S3 → EventBridge → trigger.
- **Terraform:** `plan`/`apply`, **remote state in S3 + DynamoDB locking**, modules, `for_each`, workspaces.
- Key resources: `aws_glue_job`, `aws_glue_crawler`, `aws_s3_bucket`, `aws_lakeformation_permissions`.

---

## Common gotchas

- **No state locking** → two applies corrupt the state file. Always S3 + DynamoDB.
- **Committing the state file to git** — it contains secrets and must live in the remote backend, not the repo.
- Reaching for **MWAA** when a simple **Glue Workflow** or **Step Function** would do — don't run a whole Airflow environment for three Glue jobs.
- Confusing orchestration (**when/order** things run) with processing (**what** the transform does). Airflow schedules the Glue job; the Glue job does the Spark work.

---

## Databricks translation

| Databricks | AWS-native |
|---|---|
| Databricks Jobs / Workflows | Glue Workflows / Step Functions / MWAA |
| Databricks secrets | Secrets Manager / SSM Parameter Store |

---

## Check yourself

1. Give the one-line decision rule for MWAA vs Step Functions vs Glue Workflows.
2. What's the difference between orchestration and processing?
3. What does `terraform plan` do, and why run it first?
4. What's the standard Terraform remote-state setup, and why is locking needed?
5. How do you make a pipeline start on data arrival instead of a schedule?
