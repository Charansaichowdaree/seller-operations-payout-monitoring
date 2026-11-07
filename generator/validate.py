"""CSV-level validation of PKs, FKs, enums, arithmetic and deterministic outputs."""
import csv,json,sys
from pathlib import Path

def read(folder,name):
 p=Path(folder)/f'{name}.csv'
 return list(csv.DictReader(p.open(encoding='utf-8'))) if p.exists() else []
def unique(rows,key,table,errors):
 vals=[r[key] for r in rows]
 if len(vals)!=len(set(vals)): errors.append(f'{table}.{key}: duplicate values')
def main(folder='data/generated'):
 e=[]; sellers=read(folder,'seller'); listings=read(folder,'product_listing'); orders=read(folder,'customer_order'); lines=read(folder,'order_line'); ful=read(folder,'fulfillment'); reviews=read(folder,'customer_review'); disputes=read(folder,'dispute'); rules=read(folder,'commission_rule'); payouts=read(folder,'payout'); pls=read(folder,'payout_line')
 for t,rows,k in [('seller',sellers,'seller_id'),('product_listing',listings,'listing_id'),('customer_order',orders,'order_id'),('order_line',lines,'order_line_id'),('fulfillment',ful,'fulfillment_id'),('dispute',disputes,'dispute_id'),('payout',payouts,'payout_id'),('payout_line',pls,'payout_line_id')]: unique(rows,k,t,e)
 sm={x['seller_id'] for x in sellers}; lm={x['listing_id']:x for x in listings}; om={x['order_id']:x for x in orders}; lineids={x['order_line_id'] for x in lines}; fids={x['order_line_id'] for x in ful}; pids={x['payout_id'] for x in payouts}
 for x in listings:
  if x['seller_id'] not in sm:e.append(f"Listing {x['listing_id']} missing seller")
 for x in lines:
  if x['order_id'] not in om or x['listing_id'] not in lm or x['seller_id'] not in sm:e.append(f"OrderLine {x['order_line_id']} invalid FK")
  if x['listing_id'] in lm and lm[x['listing_id']]['seller_id']!=x['seller_id']:e.append(f"OrderLine {x['order_line_id']} seller/listing mismatch")
  if round(float(x['quantity'])*float(x['unit_price']),2)!=round(float(x['line_total']),2):e.append(f"OrderLine {x['order_line_id']} arithmetic mismatch")
 line_totals={}
 for x in lines: line_totals[x['order_id']]=line_totals.get(x['order_id'],0.0)+float(x['line_total'])
 for x in orders:
  if abs(round(line_totals.get(x['order_id'],0.0),2)-float(x['order_total']))>.01:e.append(f"Order {x['order_id']} header/lines mismatch")
 for x in ful:
  if x['order_line_id'] not in lineids:e.append(f"Fulfillment {x['fulfillment_id']} invalid line")
  if x['shipped_at'] and x['delivered_at'] and x['delivered_at']<x['shipped_at']:e.append(f"Fulfillment {x['fulfillment_id']} date ordering")
  if x['shipped_at'] and (x['is_late_shipment']=='true') != (x['shipped_at']>x['promised_ship_at']):e.append(f"Fulfillment {x['fulfillment_id']} late flag mismatch")
 for x in reviews:
  if x['order_line_id'] not in fids:e.append(f"Review {x['review_id']} missing fulfillment")
 line_lookup={x['order_line_id']:x for x in lines}
 for x in disputes:
  if x['order_line_id'] not in lineids:e.append(f"Dispute {x['dispute_id']} invalid line")
  elif float(x['amount'])>float(line_lookup[x['order_line_id']]['line_total']):e.append(f"Dispute {x['dispute_id']} exceeds line value")
 for x in pls:
  if x['order_line_id'] not in lineids or x['payout_id'] not in pids:e.append(f"PayoutLine {x['payout_line_id']} invalid FK")
  expected=max(0.0,round(float(x['gross_amount'])-float(x['commission_amount'])-float(x['refund_amount'])-float(x['dispute_deduction'])-float(x['reserve_amount']),2))
  if abs(expected-float(x['net_amount']))>.01:e.append(f"PayoutLine {x['payout_line_id']} net arithmetic mismatch")
 totals={}
 for x in pls: totals[x['payout_id']]=totals.get(x['payout_id'],0.0)+float(x['net_amount'])
 for p in payouts:
  total=round(totals.get(p['payout_id'],0.0),2)
  if abs(total-float(p['payout_total']))>.01:e.append(f"Payout {p['payout_id']} header/lines mismatch")
 manifest=json.loads((Path(folder)/'source_manifest.json').read_text())
 print(json.dumps({'counts':manifest['counts'],'validation_errors':len(e),'errors':e[:30]},indent=2))
 if e: sys.exit(1)
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else 'data/generated')
