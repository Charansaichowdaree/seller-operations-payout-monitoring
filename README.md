# YottaFlex AI — Seller Operations & Payout Intelligence

A locally runnable synthetic marketplace operations platform covering seller service levels, product listings, multi-seller orders, fulfillment, reviews, disputes, commissions, reserve holds, payout eligibility and financial reconciliation.

> **Data provenance:** All generated records are fictional and created by this repository. No customer personal data or external dataset is used. Names, emails and customer IDs use reserved synthetic/test conventions.

## Architecture

- PostgreSQL 16 is the system of record (`sql/schema.sql`).
- Python generator creates deterministic CSV exports (`generator/generate.py`).
- Bulk loader imports CSVs with PostgreSQL `COPY` (`generator/load_postgres.py`).
- FastAPI exposes metrics, seller performance, exceptions and payout reconciliation (`app/main.py`).
- Streamlit + Plotly provides the operations dashboard (`dashboard/app.py`).
- Pytest covers payout calculations, hold windows and reconciliation (`tests/`).

## Quick start

Requirements: Python 3.11+, Docker Desktop / Docker Engine.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Windows PowerShell: Copy-Item .env.example .env
docker compose up -d db
```

Generate the **full target dataset** (2,000 sellers, 20,000 listings, 100,000 orders, 10,000 disputes):

```bash
python -m generator.generate --scale full --seed 20261022 --out data/generated
python -m generator.validate data/generated
python -m generator.load_postgres --input data/generated
```

Run the API and dashboard in separate terminals:

```bash
uvicorn app.main:app --reload
streamlit run dashboard/app.py
```

API docs: http://localhost:8000/docs
Dashboard: http://localhost:8501
Health check: http://localhost:8000/health

Run tests:

```bash
pytest -q
```

## Dataset reproducibility

The generator uses seed `20261022`, fixed date anchor `2026-01-01 UTC`, stable iteration order and deterministic IDs. It writes `source_manifest.json` with row counts and SHA-256 hashes. To verify reproducibility, generate twice into two separate folders and compare manifests:

```bash
python -m generator.generate --scale full --seed 20261022 --out data/run_a
python -m generator.generate --scale full --seed 20261022 --out data/run_b
python -c "import json; a=json.load(open('data/run_a/source_manifest.json')); b=json.load(open('data/run_b/source_manifest.json')); assert a['files']==b['files']; print('Reproducible: checksums match')"
```

## Database model

Ten core entities: Seller, ProductListing, Order (`customer_order`), OrderLine, Fulfillment, CustomerReview, Dispute, CommissionRule, Payout and PayoutLine. Supporting append-only history/event tables preserve seller status, fulfillment and payout state transitions. See `docs/data_dictionary.md` for field types, requiredness, enums, units, uniqueness, validation and cardinality.

## Business rules and explicit assumptions

- Multi-seller orders are split into seller-owned order lines and one fulfillment per order line.
- Late shipment is derived from actual shipment timestamp versus promised ship timestamp.
- Commission is selected by category and effective date.
- Payout eligibility is delivery timestamp + seven-day hold window.
- The illustrative reserve is 5% of gross; commission and reserve rates are configurable in `commission_rule` and the business service.
- Disputes in LOST or RESOLVED status are treated as deductible in this synthetic baseline.
- Net payout = max(0, gross − commission − refund − dispute deduction − reserve).
- All money is INR using PostgreSQL `NUMERIC`, not floating point.

These reserve/hold/dispute policies are implementation assumptions because the problem statement requires such rules but does not prescribe exact percentages, days or outcomes. They are documented in `docs/business_rules.md` and must be confirmed or adjusted if YottaFlex supplies exact policies.

## Edge cases and ground truth

`ground_truth.csv` is a separate labelled file and is not joined to operational inputs. `negative_scenarios.csv` provides five isolated, concrete negative-test fixtures with their input values and expected decisions. The ground truth documents suspended-seller active listings and the five required negative scenario classes: payout before delivery/hold release, duplicate commission, suspended seller listing, missing dispute deduction and payout header/line mismatch. Deliberately invalid negative fixtures are isolated from baseline business tables to preserve baseline referential and arithmetic integrity. Detection and expected decisions are described in the ground-truth labels.

## Validation

`generator/validate.py` checks deterministic IDs for uniqueness, foreign-key existence, seller/listing alignment, line arithmetic, fulfillment date order and payout header-to-line reconciliation. PostgreSQL constraints enforce primary keys, foreign keys, enums and numeric ranges. Additional cross-table validations are documented for review.

## Known limitations / next steps

- v1 uses one fulfillment record per order line; split parcels for one line are not yet supported.
- Returns/refunds have schema-level status coverage but do not yet have a separate refund ledger/event workflow.
- The initial API is read-focused; write endpoints and authentication are intentionally not exposed in this demo.
- The generator uses synthetic review text and test email domains only.
- Before production use, add role-based access, audit permissions, payout approval workflow, payment provider integration, full refund ledger and database migration tooling.

## Repository contents

See `docs/` for the data dictionary, business rules, architecture and prompt-history template. See `sql/schema.sql` for the executable DDL.
