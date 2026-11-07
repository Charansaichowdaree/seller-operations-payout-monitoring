# Business rules and assumptions

1. Seller status is controlled by the seller master and append-only status history. Suspended sellers cannot publish active listings; pre-existing violations are surfaced as exceptions.
2. Orders may contain lines from multiple sellers. Each line maps to exactly one seller and one listing; fulfillment is split per order line.
3. Shipment lateness is derived from `shipped_at > promised_ship_at`; delivery must not precede shipment.
4. Reviews are generated only after delivery and ratings are bounded 1–5.
5. Commission is selected by product category and effective date. The rate is stored as a fraction, e.g. 0.10 = 10%.
6. A line becomes payout-eligible only after delivery plus a seven-day hold window. This seven-day value is an explicit synthetic assumption, not a rule supplied by YottaFlex.
7. Reserve is 5% of gross in the starter policy. This is configurable and illustrative, not an externally asserted marketplace policy.
8. A LOST or RESOLVED dispute is treated as deductible in this synthetic baseline; OPEN and WON disputes are not deducted. A production implementation would distinguish refund and chargeback outcomes more precisely.
9. Net payout = max(0, gross - commission - refund - dispute deduction - reserve).
10. Payout header total must equal the sum of payout lines within INR 0.01 tolerance.
11. Ground truth is kept in a separate file/table and is never joined into operational scoring or detection features.
12. Determinism comes from a fixed random seed and stable iteration order. The generator's timestamp anchor is fixed to avoid run-time timestamps changing outputs.

## Known v1 limitations

- This synthetic version uses one fulfillment per order line; split shipment of a single line is not modelled.
- Returns are represented as a fulfillment lifecycle value in the schema but the initial generator does not create a separate return event/refund ledger.
- The generator creates synthetic customer IDs only; it does not create customer PII.
- The annual payout batch is a compact demonstration. Real marketplaces usually calculate more frequent settlement cycles and require payment-provider reconciliation.
- Required negative scenarios are recorded as isolated ground-truth test cases so deliberately invalid data does not contaminate baseline source tables.
