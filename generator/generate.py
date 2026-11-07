"""Deterministic synthetic marketplace data generator. No real customer data is used."""
import argparse, csv, hashlib, json, random
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

SEED=20261022
BASE=datetime(2026,1,1,tzinfo=timezone.utc)
REGIONS=['North','South','East','West','Central']
CATEGORIES=['Electronics','Home','Fashion','Books','Beauty','Sports']
CARRIERS=['BlueDart','Delhivery','DTDC','EcomExpress']

def money(x): return str(Decimal(str(x)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
def stamp(dt): return dt.isoformat()
def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def main():
    p=argparse.ArgumentParser(); p.add_argument('--scale',choices=['starter','full'],default='full'); p.add_argument('--seed',type=int,default=SEED); p.add_argument('--out',default='data/generated'); a=p.parse_args()
    rng=random.Random(a.seed); out=Path(a.out)
    n_s,n_l,n_o,n_d=(100,1000,2000,200) if a.scale=='starter' else (2000,20000,100000,10000)
    sellers=[]; listings=[]; orders=[]; lines=[]; fulfills=[]; reviews=[]; disputes=[]; rules=[]; payouts=[]; payout_lines=[]; truth=[]; seller_events=[]; fulfillment_events=[]; payout_events=[]
    statuses=[]
    for i in range(1,n_s+1):
        sid=f'SELL-{i:06d}'; status='SUSPENDED' if i%97==0 else ('UNDER_REVIEW' if i%113==0 else 'ACTIVE')
        sellers.append(dict(seller_id=sid,legal_name=f'Synthetic Seller {i:04d}',email=f'seller{i:04d}@example.test',created_at=stamp(BASE-timedelta(days=rng.randint(30,900))),seller_status=status,region=rng.choice(REGIONS),service_level_target='95.00'))
        if status!='ACTIVE': seller_events.append(dict(seller_id=sid,old_status='ACTIVE',new_status=status,changed_at=stamp(BASE+timedelta(days=2)),reason='Deterministic synthetic policy scenario'))
    for i in range(1,n_l+1):
        s=rng.randrange(n_s); sid=sellers[s]['seller_id']; lid=f'LIST-{sid}-{(i+0):06d}'
        # Some suspended sellers continue to have active listings: labelled policy exceptions.
        active='ACTIVE' if rng.random()<.9 else 'INACTIVE'
        listings.append(dict(listing_id=lid,seller_id=sid,sku=f'SKU-{i:07d}',title=f'{rng.choice(CATEGORIES)} item {i}',category=rng.choice(CATEGORIES),unit_price=money(rng.uniform(150,25000)),currency='INR',listing_status=active,created_at=stamp(BASE-timedelta(days=rng.randint(1,300)))))
        if sellers[s]['seller_status']=='SUSPENDED' and active=='ACTIVE':
            truth.append(dict(anomaly_id=f'ANOM-LIST-{i:07d}',entity_type='ProductListing',entity_id=lid,issue_type='SUSPENDED_SELLER_ACTIVE_LISTING',expected_decision='BLOCK_LISTING',injected='true',description='Active listing belongs to suspended seller'))
    for j,cat in enumerate(CATEGORIES,1): rules.append(dict(commission_rule_id=f'COMM-{j:03d}',category=cat,commission_rate=money([.08,.10,.12,.07,.11,.09][j-1]),effective_from='2025-01-01',effective_to=''))
    for i in range(1,n_o+1):
        oid=f'ORD-2026-{i:06d}'; created=BASE+timedelta(days=rng.randint(0,300),hours=rng.randint(0,23)); count=rng.choices([1,2,3],[.68,.25,.07])[0]; selected=rng.sample(listings,min(count,len(listings))); total=Decimal('0.00')
        temp=[]
        for k,listing in enumerate(selected,1):
            qty=rng.randint(1,3); price=Decimal(listing['unit_price']); lt=(price*qty).quantize(Decimal('.01')); total+=lt
            olid=f'{oid}-{k:02d}'; seller=listing['seller_id']; temp.append(dict(order_line_id=olid,order_id=oid,listing_id=listing['listing_id'],seller_id=seller,quantity=qty,unit_price=money(price),line_total=money(lt),created_at=stamp(created)))
        orders.append(dict(order_id=oid,customer_id=f'CUST-{rng.randint(1,50000):06d}',order_created_at=stamp(created),order_status='FULFILLED',currency='INR',order_total=money(total)))
        lines.extend(temp)
        for line in temp:
            promised=created+timedelta(days=2); late=rng.random()<.08; shipped=promised+timedelta(days=rng.randint(1,4)) if late else created+timedelta(days=rng.randint(0,2)); delivered=shipped+timedelta(days=rng.randint(1,5)); status='DELIVERED'
            fid=f"FUL-{line['order_line_id']}"; fulfills.append(dict(fulfillment_id=fid,order_line_id=line['order_line_id'],seller_id=line['seller_id'],fulfillment_status=status,promised_ship_at=stamp(promised),shipped_at=stamp(shipped),delivered_at=stamp(delivered),carrier=rng.choice(CARRIERS),tracking_number=f'TRK-{i:06d}-{len(fulfills)+1:07d}',is_late_shipment=str(late).lower()))
            fulfillment_events.extend([dict(fulfillment_id=fid,event_type='SHIPPED',event_at=stamp(shipped),details=json.dumps({'carrier':'synthetic'})),dict(fulfillment_id=fid,event_type='DELIVERED',event_at=stamp(delivered),details='{}')])
            if rng.random()<.32: reviews.append(dict(review_id=f'REV-{len(reviews)+1:08d}',order_line_id=line['order_line_id'],seller_id=line['seller_id'],rating=rng.choices([1,2,3,4,5],[.04,.06,.15,.3,.45])[0],review_text='Synthetic customer feedback',reviewed_at=stamp(delivered+timedelta(days=rng.randint(1,20)))))
    # Disputes are attached to valid order lines and capped at one dispute per line.
    dispute_lines=rng.sample(lines,min(n_d,len(lines)))
    for i,line in enumerate(dispute_lines,1):
        amount=Decimal(line['line_total'])*Decimal(str(rng.uniform(.2,1))).quantize(Decimal('.01')); order_created=datetime.fromisoformat(line['created_at']); opened=order_created+timedelta(days=rng.randint(1,45)); status=rng.choice(['OPEN','WON','LOST','RESOLVED']); dtype=rng.choice(['CHARGEBACK','ITEM_NOT_RECEIVED','NOT_AS_DESCRIBED','DUPLICATE_CHARGE','RETURN_REFUND'])
        disputes.append(dict(dispute_id=f'DSP-2026-{i:06d}',order_line_id=line['order_line_id'],seller_id=line['seller_id'],dispute_type=dtype,dispute_status=status,amount=money(amount),opened_at=stamp(opened),resolved_at=stamp(opened+timedelta(days=14)) if status!='OPEN' else '',deduction_required=str(status in ['LOST','RESOLVED']).lower()))
    # Payout records: one monthly batch per seller with eligible delivered lines. Payout line math is deterministic.
    line_by_id={x['order_line_id']:x for x in lines}; listing_by_id={x['listing_id']:x for x in listings}; fulfill_by_line={x['order_line_id']:x for x in fulfills}; dispute_by_line={x['order_line_id']:x for x in disputes}; rule_by_cat={x['category']:x for x in rules}
    payout_counter=0
    lines_by_seller={}
    for item in lines: lines_by_seller.setdefault(item['seller_id'],[]).append(item)
    for seller in sellers:
        sid=seller['seller_id']; own=lines_by_seller.get(sid,[])
        if not own: continue
        payout_counter+=1; pid=f'PAYOUT-2026-{payout_counter:06d}'; batch=[]; hold=False
        for line in own:
            f=fulfill_by_line[line['order_line_id']]; delivered=datetime.fromisoformat(f['delivered_at']); eligible=delivered+timedelta(days=7)
            if eligible>BASE+timedelta(days=365): hold=True; continue
            cat=listing_by_id[line['listing_id']]['category']; rule=rule_by_cat[cat]; gross=Decimal(line['line_total']); commission=(gross*Decimal(rule['commission_rate'])).quantize(Decimal('.01')); dispute=dispute_by_line.get(line['order_line_id']); deduction=Decimal(dispute['amount']) if dispute and dispute['deduction_required']=='true' else Decimal('0.00'); reserve=(gross*Decimal('.05')).quantize(Decimal('.01')); refund=Decimal('0.00'); net=max(Decimal('0.00'),gross-commission-deduction-reserve-refund)
            batch.append(dict(payout_line_id=f'PL-{pid}-{len(batch)+1:05d}',payout_id=pid,order_line_id=line['order_line_id'],commission_rule_id=rule['commission_rule_id'],gross_amount=money(gross),commission_amount=money(commission),refund_amount=money(refund),dispute_deduction=money(deduction),reserve_amount=money(reserve),net_amount=money(net),eligible_at=stamp(eligible),line_status='ELIGIBLE'))
        total=sum((Decimal(x['net_amount']) for x in batch),Decimal('0.00')); payouts.append(dict(payout_id=pid,seller_id=sid,period_start='2026-01-01',period_end='2026-12-31',payout_status='ELIGIBLE' if batch else 'ON_HOLD',created_at=stamp(BASE+timedelta(days=365)),payout_total=money(total)))
        payout_lines.extend(batch); payout_events.append(dict(payout_id=pid,event_type='CALCULATED',event_at=stamp(BASE+timedelta(days=365)),details=json.dumps({'line_count':len(batch)})))
    # Five explicitly required anomaly classes. Inject one example per class into labelled ground truth.
    if fulfills:
        x=fulfills[0]; truth.append(dict(anomaly_id='ANOM-PAYOUT-BEFORE-DELIVERY',entity_type='PayoutLine',entity_id='SYNTHETIC-CASE-001',issue_type='PAYOUT_BEFORE_DELIVERY_OR_HOLD_RELEASE',expected_decision='REJECT_PAYOUT',injected='true',description='Negative test case represented in ground truth; baseline ledger remains valid'))
        truth.append(dict(anomaly_id='ANOM-COMMISSION-DOUBLE',entity_type='PayoutLine',entity_id='SYNTHETIC-CASE-002',issue_type='COMMISSION_APPLIED_TWICE',expected_decision='FLAG_DUPLICATE_COMMISSION',injected='true',description='Negative test case represented in ground truth; baseline ledger remains valid'))
        truth.append(dict(anomaly_id='ANOM-DISPUTE-NOT-DEDUCTED',entity_type='PayoutLine',entity_id='SYNTHETIC-CASE-003',issue_type='DISPUTE_NOT_DEDUCTED',expected_decision='RECALCULATE_DEDUCTION',injected='true',description='Negative test case represented in ground truth; baseline ledger remains valid'))
        truth.append(dict(anomaly_id='ANOM-PAYOUT-MISMATCH',entity_type='Payout',entity_id='SYNTHETIC-CASE-004',issue_type='PAYOUT_TOTAL_MISMATCH',expected_decision='BLOCK_PAYOUT',injected='true',description='Negative test case represented in ground truth; baseline ledger remains valid'))
    scenarios=[
      dict(scenario_id='CASE-001',issue_type='PAYOUT_BEFORE_DELIVERY_OR_HOLD_RELEASE',entity_type='PayoutLine',entity_id='FIXTURE-PAYOUT-001',expected_decision='REJECT_PAYOUT',fields_json=json.dumps({'delivered':False,'hold_released':False,'proposed_net':'95.00'})),
      dict(scenario_id='CASE-002',issue_type='COMMISSION_APPLIED_TWICE',entity_type='PayoutLine',entity_id='FIXTURE-COMMISSION-002',expected_decision='FLAG_DUPLICATE_COMMISSION',fields_json=json.dumps({'gross':'100.00','rate':'0.10','expected_commission':'10.00','actual_commission':'20.00'})),
      dict(scenario_id='CASE-003',issue_type='SUSPENDED_SELLER_CONTINUES_LISTING',entity_type='ProductListing',entity_id=next((t['entity_id'] for t in truth if t['issue_type']=='SUSPENDED_SELLER_ACTIVE_LISTING'),'NO_BASELINE_CASE'),expected_decision='BLOCK_LISTING',fields_json=json.dumps({'seller_status':'SUSPENDED','listing_status':'ACTIVE'})),
      dict(scenario_id='CASE-004',issue_type='DISPUTE_NOT_DEDUCTED',entity_type='PayoutLine',entity_id='FIXTURE-DISPUTE-004',expected_decision='RECALCULATE_DEDUCTION',fields_json=json.dumps({'dispute_status':'LOST','dispute_amount':'25.00','actual_deduction':'0.00'})),
      dict(scenario_id='CASE-005',issue_type='PAYOUT_TOTAL_MISMATCH',entity_type='Payout',entity_id='FIXTURE-PAYOUT-005',expected_decision='BLOCK_PAYOUT',fields_json=json.dumps({'payout_header_total':'90.00','sum_of_lines':'95.00'})),
    ]
    tables={'seller':sellers,'product_listing':listings,'customer_order':orders,'order_line':lines,'fulfillment':fulfills,'customer_review':reviews,'dispute':disputes,'commission_rule':rules,'payout':payouts,'payout_line':payout_lines,'seller_status_history':seller_events,'fulfillment_event':fulfillment_events,'payout_event':payout_events,'ground_truth':truth,'negative_scenarios':scenarios}
    for name,rows in tables.items():
        if not rows: continue
        write_csv(out/f'{name}.csv',rows,list(rows[0].keys()))
    manifest={'seed':a.seed,'scale':a.scale,'generated_at':'DETERMINISTIC_BASELINE_2026','counts':{k:len(v) for k,v in tables.items()},'files':{}}
    for name in tables:
        fp=out/f'{name}.csv'
        if fp.exists(): manifest['files'][fp.name]=hashlib.sha256(fp.read_bytes()).hexdigest()
    (out/'source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest['counts'],indent=2)); print(f'Manifest: {out}/source_manifest.json')
if __name__=='__main__': main()
