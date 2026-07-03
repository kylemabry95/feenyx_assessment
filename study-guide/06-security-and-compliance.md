# 06 — Security & Compliance

Prereqs: [03 — S3](03-amazon-s3.md), [05 — Lake Formation](05-warehousing-and-lakes.md). For a Federal/DoD-flavored role, this is a make-or-break chapter — and it's where your GovCloud/FedRAMP experience is a genuine differentiator.

---

## In plain English

Security in data engineering answers three questions for **every** piece of data:

1. **Is it encrypted?** (Both sitting in storage and moving over the network.)
2. **Who can access it?** (As few people/roles as possible — "least privilege.")
3. **Can we prove who did what?** (An audit trail for compliance.)

For sensitive government data (**CUI** — Controlled Unclassified Information, and **PII** — Personally Identifiable Information), the bar is higher and legally mandated.

---

## Encryption

- **At rest** — data on disk is encrypted. In S3 that's **SSE-KMS**, ideally with **customer-managed keys (CMKs)** so *you* control the key policy and get an audit trail of key usage.
- **In transit** — data moving over the network is encrypted with **TLS (HTTPS)**. Enforce it so nothing travels in plaintext.

### KMS (Key Management Service)

The service that manages encryption keys. Concepts to know:

- **Envelope encryption** — KMS doesn't encrypt your big data directly. It generates a **data key** to encrypt the data, then encrypts *that key* with a master key. Efficient and secure.
- **Key policies vs IAM** — a KMS key has its own resource policy (**key policy**) controlling who can use it, layered with IAM. For sensitive data you scope tightly.
- **Cross-account grants** — allow another account to use a key without sharing it outright.
- **Automatic rotation** — CMKs can auto-rotate on a schedule, a common compliance requirement.

**Why CMKs matter for CUI:** with a customer-managed key you control exactly who can decrypt, and every use is logged — you can *prove* access control to an auditor.

---

## Access control — least privilege

- **IAM (Identity and Access Management)** — the core AWS permissions system. **Least privilege** means each role gets the *minimum* permissions needed, nothing more. Default-deny.
- **Lake Formation** (from [chapter 05](05-warehousing-and-lakes.md)) — layer on **column/row/cell-level grants** so, e.g., analysts can query a table but not see the SSN column.
- **VPC endpoints** — keep traffic to S3/other services on Amazon's private network so **data never traverses the public internet.** A frequent compliance requirement.
- **Tagging for data classification** — tag data assets (`classification=CUI`) and drive access decisions off tags (LF-Tags / TBAC).

---

## Amazon Macie — find the sensitive data

**Macie uses machine learning to automatically discover sensitive data (PII, credentials, financial info) in S3 specifically.** It scans your buckets and produces **findings** ("this object contains SSNs"), which flow to **EventBridge** so you can auto-remediate (quarantine the file, alert security, etc.).

> **Exam trigger phrase:** "automatically discover PII in S3" → **Macie.** (S3 is the key qualifier — Macie is S3-focused.)

A typical pattern: Macie scans the raw zone → finding → EventBridge → Lambda quarantines or masks the data before it can move downstream.

---

## Audit trail stack — proving who did what

Compliance requires you to reconstruct history. The AWS audit stack:

- **CloudTrail** — logs every **API call** in the account ("who called `DeleteObject` and when"). Enable **S3 data events** to log object-level reads/writes too.
- **CloudWatch Logs** — application and service logs, metrics, alarms.
- **AWS Config** — tracks **resource configuration state over time** ("was this bucket ever public?"). Configuration history + compliance rules.
- **Lake Formation / Athena query logs** — who queried what data.

Together these let you answer any "who touched this data" question an auditor asks.

---

## Handling CUI/PII securely — the full checklist

This is the long-form answer to "how do you handle sensitive data?" Cover:

1. **Boundary & baseline** — **GovCloud** region + **FedRAMP High** baseline; **NIST 800-171** as the CUI control framework.
2. **Encryption** — **KMS CMKs** with tight key policies; **TLS everywhere.**
3. **Network isolation** — **VPC endpoints**, no public internet path.
4. **Access control** — **IAM least privilege** + **Lake Formation** column/row-level grants.
5. **Discovery** — **Macie** automated PII scanning → EventBridge remediation.
6. **Audit** — **CloudTrail (+ S3 data events)**, AWS Config, query logs.
7. **Non-prod safety** — **tokenization/masking** so real PII never lands in dev/test.
8. **Classification** — **tagging** so access and lifecycle follow the data's sensitivity.

---

## Key facts to memorize

- Encrypt **at rest (SSE-KMS + CMKs)** and **in transit (TLS).**
- **KMS:** envelope encryption, key policies vs IAM, cross-account grants, auto-rotation.
- **Least privilege IAM** + **Lake Formation** fine-grained grants + **VPC endpoints** (no public internet).
- **Macie** = ML-based **PII discovery in S3** → EventBridge remediation. Trigger: "discover PII in S3."
- **Audit stack:** CloudTrail (API calls, + S3 data events), CloudWatch Logs, AWS Config (resource state), query logs.
- **CUI baseline:** GovCloud + FedRAMP High + **NIST 800-171.**

---

## Common gotchas

- Confusing **Macie (S3 PII discovery)** with **GuardDuty (threat detection from logs)** and **Inspector (vulnerability scanning)**. Macie = sensitive *data*, GuardDuty = malicious *activity*, Inspector = software *vulnerabilities*.
- Thinking SSE-S3 is enough for CUI — you generally want **SSE-KMS with CMKs** for the access control and audit trail.
- Forgetting **S3 data events** in CloudTrail — without them you log the management API but not object reads/writes.
- Leaving real PII in **non-prod** — mask/tokenize it.

---

## Your differentiator (use this in the interview)

Most candidates have never touched FedRAMP High or GovCloud. Ground your answers in real work: the **GuardDuty centralization architecture** (EventBridge + Lambda + S3 across accounts) proves you've *built* security plumbing, not just consumed it. NIST 800-171 for CUI, GovCloud boundaries, and CMK key policies are things you can speak to from experience — lean in hard here.

---

## Check yourself

1. What's the difference between encryption at rest and in transit, and which S3 option do you use for CUI?
2. What is envelope encryption?
3. Which service discovers PII in S3, and what does it trigger?
4. Name three components of the AWS audit trail and what each captures.
5. Distinguish Macie, GuardDuty, and Inspector in one line each.
