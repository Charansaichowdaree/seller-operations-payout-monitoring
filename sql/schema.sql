CREATE TABLE IF NOT EXISTS seller (
 seller_id TEXT PRIMARY KEY, legal_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 created_at TIMESTAMPTZ NOT NULL, seller_status TEXT NOT NULL CHECK (seller_status IN ('ACTIVE','SUSPENDED','UNDER_REVIEW','CLOSED')),
 region TEXT NOT NULL, service_level_target NUMERIC(5,2) NOT NULL CHECK(service_level_target BETWEEN 0 AND 100)
);
CREATE TABLE IF NOT EXISTS product_listing (
 listing_id TEXT PRIMARY KEY, seller_id TEXT NOT NULL REFERENCES seller(seller_id), sku TEXT NOT NULL,
 title TEXT NOT NULL, category TEXT NOT NULL, unit_price NUMERIC(12,2) NOT NULL CHECK(unit_price >= 0),
 currency CHAR(3) NOT NULL DEFAULT 'INR', listing_status TEXT NOT NULL CHECK(listing_status IN ('ACTIVE','INACTIVE','REMOVED')),
 created_at TIMESTAMPTZ NOT NULL, UNIQUE(seller_id,sku)
);
CREATE TABLE IF NOT EXISTS customer_order (
 order_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, order_created_at TIMESTAMPTZ NOT NULL,
 order_status TEXT NOT NULL CHECK(order_status IN ('PLACED','PARTIALLY_FULFILLED','FULFILLED','CANCELLED','RETURNED')),
 currency CHAR(3) NOT NULL DEFAULT 'INR', order_total NUMERIC(14,2) NOT NULL CHECK(order_total >= 0)
);
CREATE TABLE IF NOT EXISTS order_line (
 order_line_id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES customer_order(order_id),
 listing_id TEXT NOT NULL REFERENCES product_listing(listing_id), seller_id TEXT NOT NULL REFERENCES seller(seller_id),
 quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price NUMERIC(12,2) NOT NULL CHECK(unit_price >= 0),
 line_total NUMERIC(14,2) NOT NULL CHECK(line_total >= 0), created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS fulfillment (
 fulfillment_id TEXT PRIMARY KEY, order_line_id TEXT NOT NULL UNIQUE REFERENCES order_line(order_line_id),
 seller_id TEXT NOT NULL REFERENCES seller(seller_id), fulfillment_status TEXT NOT NULL CHECK(fulfillment_status IN ('PENDING','SHIPPED','DELIVERED','RETURNED','CANCELLED')),
 promised_ship_at TIMESTAMPTZ NOT NULL, shipped_at TIMESTAMPTZ, delivered_at TIMESTAMPTZ,
 carrier TEXT NOT NULL, tracking_number TEXT NOT NULL UNIQUE, is_late_shipment BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS customer_review (
 review_id TEXT PRIMARY KEY, order_line_id TEXT NOT NULL UNIQUE REFERENCES order_line(order_line_id),
 seller_id TEXT NOT NULL REFERENCES seller(seller_id), rating SMALLINT NOT NULL CHECK(rating BETWEEN 1 AND 5),
 review_text TEXT, reviewed_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS dispute (
 dispute_id TEXT PRIMARY KEY, order_line_id TEXT NOT NULL REFERENCES order_line(order_line_id),
 seller_id TEXT NOT NULL REFERENCES seller(seller_id), dispute_type TEXT NOT NULL CHECK(dispute_type IN ('CHARGEBACK','ITEM_NOT_RECEIVED','NOT_AS_DESCRIBED','DUPLICATE_CHARGE','RETURN_REFUND')),
 dispute_status TEXT NOT NULL CHECK(dispute_status IN ('OPEN','WON','LOST','RESOLVED')), amount NUMERIC(12,2) NOT NULL CHECK(amount > 0),
 opened_at TIMESTAMPTZ NOT NULL, resolved_at TIMESTAMPTZ, deduction_required BOOLEAN NOT NULL
);
CREATE TABLE IF NOT EXISTS commission_rule (
 commission_rule_id TEXT PRIMARY KEY, category TEXT NOT NULL, commission_rate NUMERIC(6,5) NOT NULL CHECK(commission_rate BETWEEN 0 AND 1),
 effective_from DATE NOT NULL, effective_to DATE, CHECK(effective_to IS NULL OR effective_to > effective_from)
);
CREATE TABLE IF NOT EXISTS payout (
 payout_id TEXT PRIMARY KEY, seller_id TEXT NOT NULL REFERENCES seller(seller_id), period_start DATE NOT NULL,
 period_end DATE NOT NULL, payout_status TEXT NOT NULL CHECK(payout_status IN ('DRAFT','ELIGIBLE','ON_HOLD','PAID','REJECTED')),
 created_at TIMESTAMPTZ NOT NULL, payout_total NUMERIC(14,2) NOT NULL DEFAULT 0,
 CHECK(period_end >= period_start)
);
CREATE TABLE IF NOT EXISTS payout_line (
 payout_line_id TEXT PRIMARY KEY, payout_id TEXT NOT NULL REFERENCES payout(payout_id),
 order_line_id TEXT NOT NULL REFERENCES order_line(order_line_id), commission_rule_id TEXT NOT NULL REFERENCES commission_rule(commission_rule_id),
 gross_amount NUMERIC(14,2) NOT NULL, commission_amount NUMERIC(14,2) NOT NULL,
 refund_amount NUMERIC(14,2) NOT NULL DEFAULT 0, dispute_deduction NUMERIC(14,2) NOT NULL DEFAULT 0,
 reserve_amount NUMERIC(14,2) NOT NULL DEFAULT 0, net_amount NUMERIC(14,2) NOT NULL,
 eligible_at TIMESTAMPTZ NOT NULL, line_status TEXT NOT NULL CHECK(line_status IN ('ELIGIBLE','ON_HOLD','PAID')),
 UNIQUE(payout_id,order_line_id)
);
CREATE TABLE IF NOT EXISTS seller_status_history (
 event_id BIGSERIAL PRIMARY KEY, seller_id TEXT NOT NULL REFERENCES seller(seller_id), old_status TEXT,
 new_status TEXT NOT NULL, changed_at TIMESTAMPTZ NOT NULL, reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fulfillment_event (
 event_id BIGSERIAL PRIMARY KEY, fulfillment_id TEXT NOT NULL REFERENCES fulfillment(fulfillment_id),
 event_type TEXT NOT NULL, event_at TIMESTAMPTZ NOT NULL, details JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS payout_event (
 event_id BIGSERIAL PRIMARY KEY, payout_id TEXT NOT NULL REFERENCES payout(payout_id),
 event_type TEXT NOT NULL, event_at TIMESTAMPTZ NOT NULL, details JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS ground_truth (
 anomaly_id TEXT PRIMARY KEY, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, issue_type TEXT NOT NULL,
 expected_decision TEXT NOT NULL, injected BOOLEAN NOT NULL DEFAULT TRUE, description TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_listing_seller ON product_listing(seller_id);
CREATE INDEX IF NOT EXISTS idx_orderline_order ON order_line(order_id);
CREATE INDEX IF NOT EXISTS idx_orderline_seller ON order_line(seller_id);
CREATE INDEX IF NOT EXISTS idx_fulfillment_seller_status ON fulfillment(seller_id,fulfillment_status);
CREATE INDEX IF NOT EXISTS idx_dispute_seller_status ON dispute(seller_id,dispute_status);
CREATE INDEX IF NOT EXISTS idx_payout_seller ON payout(seller_id);
CREATE INDEX IF NOT EXISTS idx_payoutline_orderline ON payout_line(order_line_id);
