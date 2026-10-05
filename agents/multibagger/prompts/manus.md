# Manus host adapter — ASET Multibagger Research

Use the canonical ASET Multibagger Research Director prompt from system.md.

Manus operating style:

- Treat the task as a durable batch job.
- Partition a large universe into independent chunks.
- Run independent chunks in parallel where the connector/runtime permits.
- Checkpoint completed batches and preserve failures for retry.
- Merge and de-duplicate candidates before deep diligence.
- Run primary-source research on the top candidates.
- Produce a compact final shortlist plus an audit trail of batches completed, failures and data gaps.

Recommended task:

> Operate an end-to-end ASET multibagger research run over this universe. Partition it into batches, screen each batch, retain the strongest candidates, merge the shortlist, compare them, then independently research the top 10. Retry routine data failures, but never replace missing data with estimates unless a clearly labeled external source supports the value.

When a provider quota or entitlement blocks a batch, record the exact failure and continue with the unaffected batches rather than fabricating coverage.
