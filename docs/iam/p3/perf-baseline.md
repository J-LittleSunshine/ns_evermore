# IAM Performance Baseline (P3)

## 1. Core Metrics

- `authorize/check` latency (P50/P95)
- `authorize/batch-check` throughput
- ACL query latency
- policy rule match latency
- decision audit write latency

## 2. Suggested Baseline Targets

- Single check P95 <= 30ms (intra-VPC)
- Batch check (100 items) <= 300ms
- Decision audit write success >= 99.9%

## 3. Benchmark Dimensions

- Subject count: user + role + org + dept + subsidiary combinations
- Policy rule count: 1k / 10k / 50k
- ACL row count: 10k / 100k / 1M

## 4. Optimization Checklist

- Ensure composite indexes for subject/resource/action and rule priority.
- Keep policy-rule payload lightweight (`condition_json` only needed fields).
- Avoid synchronous external IO in authorization hot path.

