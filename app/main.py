from fastapi import FastAPI, HTTPException
from app.db import connect, init_db
app=FastAPI(title='YottaFlex Seller Operations API',version='1.0.0',description='Seller service levels, fulfillment, disputes, commissions and payout monitoring')
@app.on_event('startup')
def startup():
    try: init_db()
    except Exception as exc: print(f'Database initialization skipped: {exc}')
@app.get('/health')
def health():
    try:
        with connect() as c: c.execute('SELECT 1')
        return {'status':'ok','database':'connected'}
    except Exception as e: raise HTTPException(503,detail=f'Database unavailable: {e}')
@app.get('/metrics/overview')
def overview():
    q='''SELECT (SELECT count(*) FROM seller) sellers,(SELECT count(*) FROM product_listing) listings,(SELECT count(*) FROM customer_order) orders,(SELECT count(*) FROM dispute) disputes,(SELECT count(*) FROM payout) payouts,(SELECT coalesce(sum(payout_total),0) FROM payout) payout_value'''
    with connect() as c: return dict(c.execute(q).fetchone())
@app.get('/sellers')
def sellers(limit:int=100, offset:int=0, status:str|None=None):
    if limit<1 or limit>1000: raise HTTPException(400,'limit must be 1..1000')
    q='SELECT seller_id,legal_name,seller_status,region FROM seller WHERE (%s IS NULL OR seller_status=%s) ORDER BY seller_id LIMIT %s OFFSET %s'
    with connect() as c: return [dict(r) for r in c.execute(q,(status,status,limit,offset)).fetchall()]
@app.get('/sellers/{seller_id}/performance')
def seller_performance(seller_id:str):
    q='''SELECT s.seller_id,s.legal_name,s.seller_status,count(DISTINCT f.fulfillment_id) fulfillment_count, count(DISTINCT f.fulfillment_id) FILTER (WHERE f.is_late_shipment) late_shipments, round(100.0*count(DISTINCT f.fulfillment_id) FILTER (WHERE NOT f.is_late_shipment)/nullif(count(DISTINCT f.fulfillment_id),0),2) on_time_ship_rate, round(avg(r.rating)::numeric,2) avg_rating, count(DISTINCT d.dispute_id) disputes FROM seller s LEFT JOIN fulfillment f ON f.seller_id=s.seller_id LEFT JOIN customer_review r ON r.seller_id=s.seller_id LEFT JOIN dispute d ON d.seller_id=s.seller_id WHERE s.seller_id=%s GROUP BY s.seller_id'''
    with connect() as c: row=c.execute(q,(seller_id,)).fetchone()
    if not row: raise HTTPException(404,'Seller not found')
    return dict(row)
@app.get('/exceptions')
def exceptions():
    q='''SELECT 'SUSPENDED_SELLER_ACTIVE_LISTING' issue_type,l.listing_id entity_id,'BLOCK_LISTING' expected_decision FROM product_listing l JOIN seller s USING(seller_id) WHERE s.seller_status='SUSPENDED' AND l.listing_status='ACTIVE' UNION ALL SELECT 'PAYOUT_TOTAL_MISMATCH',p.payout_id,'BLOCK_PAYOUT' FROM payout p LEFT JOIN (SELECT payout_id,sum(net_amount) total FROM payout_line GROUP BY payout_id) x USING(payout_id) WHERE abs(p.payout_total-coalesce(x.total,0))>0.01'''
    with connect() as c: return [dict(r) for r in c.execute(q).fetchall()]
@app.get('/payouts/{payout_id}/reconciliation')
def reconcile(payout_id:str):
    q='''SELECT p.payout_id,p.payout_total,coalesce(sum(pl.net_amount),0) line_total,(p.payout_total-coalesce(sum(pl.net_amount),0)) difference,abs(p.payout_total-coalesce(sum(pl.net_amount),0))<0.01 reconciled FROM payout p LEFT JOIN payout_line pl USING(payout_id) WHERE p.payout_id=%s GROUP BY p.payout_id'''
    with connect() as c: row=c.execute(q,(payout_id,)).fetchone()
    if not row: raise HTTPException(404,'Payout not found')
    return dict(row)
