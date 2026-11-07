# Data dictionary

All money is INR in `NUMERIC(...,2)`; timestamps are UTC `TIMESTAMPTZ`; dates are ISO-8601. IDs are immutable strings. Required means `NOT NULL` unless a documented optional field is nullable.

| Entity / field | Type | Req.? | Allowed values / unit | Uniqueness | Validation |
|---|---|---:|---|---|---|
| Seller.seller_id | TEXT | Yes | `SELL-000001` | PK | Immutable deterministic ID |
| Seller.legal_name | TEXT | Yes | Synthetic legal name | No | Non-empty |
| Seller.email | TEXT | Yes | `.example.test` synthetic email | Unique | Valid synthetic email |
| Seller.created_at | TIMESTAMPTZ | Yes | UTC | No | Not in future relative to generation anchor |
| Seller.seller_status | TEXT | Yes | ACTIVE, SUSPENDED, UNDER_REVIEW, CLOSED | No | Enum; changes recorded in seller_status_history |
| Seller.region | TEXT | Yes | North, South, East, West, Central | No | Enum |
| Seller.service_level_target | NUMERIC(5,2) | Yes | 0–100 percent | No | Range check |
| ProductListing.listing_id | TEXT | Yes | `LIST-<seller-id>-000001` | PK | Seller ID segment must match FK |
| ProductListing.seller_id | TEXT | Yes | Seller FK | No | Parent seller exists |
| ProductListing.sku | TEXT | Yes | Synthetic SKU | Unique per seller | `(seller_id,sku)` unique |
| ProductListing.title/category | TEXT | Yes | Product title / category enum | No | Non-empty; category matches commission rule |
| ProductListing.unit_price | NUMERIC(12,2) | Yes | INR | No | >= 0 |
| ProductListing.currency | CHAR(3) | Yes | INR | No | ISO currency code |
| ProductListing.listing_status | TEXT | Yes | ACTIVE, INACTIVE, REMOVED | No | Suspended sellers may not create/retain ACTIVE listings; anomaly labelled |
| ProductListing.created_at | TIMESTAMPTZ | Yes | UTC | No | Valid timestamp |
| Order.order_id | TEXT | Yes | `ORD-2026-000001` | PK | Immutable deterministic ID |
| Order.customer_id | TEXT | Yes | Synthetic `CUST-*` | No | Never identifies a real person |
| Order.order_created_at | TIMESTAMPTZ | Yes | UTC | No | Before fulfillment events |
| Order.order_status | TEXT | Yes | PLACED, PARTIALLY_FULFILLED, FULFILLED, CANCELLED, RETURNED | No | Lifecycle enum |
| Order.currency/order_total | CHAR(3)/NUMERIC(14,2) | Yes | INR / INR | No | Total equals sum of order lines |
| OrderLine.order_line_id | TEXT | Yes | `<order-id>-01` | PK | Unique immutable ID |
| OrderLine.order_id | TEXT | Yes | Order FK | No | Parent exists |
| OrderLine.listing_id/seller_id | TEXT | Yes | Listing and Seller FKs | No | Listing seller must equal line seller |
| OrderLine.quantity | INTEGER | Yes | Units | No | > 0 |
| OrderLine.unit_price/line_total | NUMERIC | Yes | INR | No | line_total = quantity × unit_price |
| Fulfillment.fulfillment_id | TEXT | Yes | `FUL-<order-line-id>` | PK | Deterministic from line ID |
| Fulfillment.order_line_id | TEXT | Yes | OrderLine FK | Unique | One fulfillment per line in v1 |
| Fulfillment.seller_id | TEXT | Yes | Seller FK | No | Matches order line seller |
| Fulfillment.fulfillment_status | TEXT | Yes | PENDING, SHIPPED, DELIVERED, RETURNED, CANCELLED | No | Lifecycle transitions only |
| Fulfillment.promised_ship_at/shipped_at/delivered_at | TIMESTAMPTZ | Required/optional/optional | UTC | No | promised <= shipped <= delivered |
| Fulfillment.carrier/tracking_number | TEXT | Yes | Synthetic carrier/tracking | Tracking unique | Non-empty |
| Fulfillment.is_late_shipment | BOOLEAN | Yes | true/false | No | Derived: shipped_at > promised_ship_at |
| CustomerReview.review_id | TEXT | Yes | `REV-00000001` | PK | Immutable |
| CustomerReview.order_line_id | TEXT | Yes | OrderLine FK | Unique | Review only after delivery |
| CustomerReview.seller_id | TEXT | Yes | Seller FK | No | Matches line seller |
| CustomerReview.rating | SMALLINT | Yes | 1–5 stars | No | Range check |
| CustomerReview.review_text | TEXT | No | Synthetic text | No | No personal data |
| CustomerReview.reviewed_at | TIMESTAMPTZ | Yes | UTC | No | >= delivered_at |
| Dispute.dispute_id | TEXT | Yes | `DSP-2026-000001` | PK | Immutable deterministic ID |
| Dispute.order_line_id/seller_id | TEXT | Yes | OrderLine/Seller FKs | No | Seller matches line seller |
| Dispute.dispute_type | TEXT | Yes | CHARGEBACK, ITEM_NOT_RECEIVED, NOT_AS_DESCRIBED, DUPLICATE_CHARGE, RETURN_REFUND | No | Enum |
| Dispute.dispute_status | TEXT | Yes | OPEN, WON, LOST, RESOLVED | No | Lifecycle enum |
| Dispute.amount | NUMERIC(12,2) | Yes | INR | No | > 0 and <= line total |
| Dispute.opened_at/resolved_at | TIMESTAMPTZ | Yes/No | UTC | No | resolved >= opened |
| Dispute.deduction_required | BOOLEAN | Yes | true/false | No | Derived from outcome policy |
| CommissionRule.commission_rule_id | TEXT | Yes | `COMM-001` | PK | Immutable |
| CommissionRule.category | TEXT | Yes | Product category | No | Category enum |
| CommissionRule.commission_rate | NUMERIC(6,5) | Yes | Fraction 0–1 | No | Effective-dated rule |
| CommissionRule.effective_from/effective_to | DATE | Yes/No | Inclusive start, exclusive end | No | end > start; no overlapping rules per category |
| Payout.payout_id | TEXT | Yes | `PAYOUT-2026-000001` | PK | Immutable |
| Payout.seller_id | TEXT | Yes | Seller FK | No | Seller exists |
| Payout.period_start/period_end | DATE | Yes | Calendar dates | No | end >= start |
| Payout.payout_status | TEXT | Yes | DRAFT, ELIGIBLE, ON_HOLD, PAID, REJECTED | No | Derived from line eligibility |
| Payout.created_at | TIMESTAMPTZ | Yes | UTC | No | >= period end in generated annual batch |
| Payout.payout_total | NUMERIC(14,2) | Yes | INR | No | Equals sum of payout lines |
| PayoutLine.payout_line_id | TEXT | Yes | `PL-<payout-id>-00001` | PK | Immutable |
| PayoutLine.payout_id/order_line_id/commission_rule_id | TEXT | Yes | FKs | `(payout_id,order_line_id)` unique | All parents exist; seller alignment checked |
| PayoutLine.gross/commission/refund/dispute/reserve/net | NUMERIC(14,2) | Yes | INR | No | net = max(0,gross - all deductions) |
| PayoutLine.eligible_at | TIMESTAMPTZ | Yes | UTC | No | delivered_at + configured hold days |
| PayoutLine.line_status | TEXT | Yes | ELIGIBLE, ON_HOLD, PAID | No | Cannot be ELIGIBLE before hold release |
| Event history tables | BIGSERIAL + FK + timestamp + JSONB | Yes | Event-specific | PK | Append-only; no destructive state overwrite |
| GroundTruth | TEXT IDs + labels | Yes | issue_type and expected_decision | PK | Separate from operational feature inputs |

## Cardinality and optionality

- Seller 1:N ProductListing, OrderLine, Dispute, Payout and review records.
- Order 1:N OrderLine; ProductListing 1:N OrderLine. Together these form the order-to-listing N:M relationship through OrderLine.
- OrderLine 1:0..1 Fulfillment and 1:0..1 CustomerReview in this first version.
- Seller 1:N Payout; Payout 1:N PayoutLine; OrderLine 1:N Dispute (multiple disputes may be recorded over time).
- CommissionRule 1:N PayoutLine over effective periods.
- State history is 1:N from Seller/Fulfillment/Payout to event rows.
