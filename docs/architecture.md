# Architecture and traceability

```text
Synthetic generator -> CSV/JSON exports -> PostgreSQL
                                      |       |
                                      |       +-> FastAPI read API
                                      |       +-> Streamlit dashboard
                                      +-> ground_truth (isolated labels)
```

PostgreSQL is authoritative. Every transaction row references a parent ID. OrderLine resolves the Order↔ProductListing many-to-many relationship and carries the seller ownership key for seller-level settlement. Fulfillment and payout state history are append-only supporting records. Financial outputs are derived from source order lines, effective-dated commission rules, delivery timestamps, disputes and configured holds.

## Traceability chain

`Seller -> ProductListing -> OrderLine -> Order -> Fulfillment -> Dispute/Review -> CommissionRule -> PayoutLine -> Payout`.

The ID convention is deterministic and stable: `SELL-000001`, `LIST-<seller-id>-000001`, `ORD-2026-000001`, `FUL-<order-line-id>`, `DSP-2026-000001`, `PAYOUT-2026-000001`.
