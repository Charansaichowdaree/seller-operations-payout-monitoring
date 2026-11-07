"""Load generated CSV tables into PostgreSQL using COPY for efficient bulk ingestion."""
import argparse,csv
from pathlib import Path
import psycopg
from app.db import DATABASE_URL,init_db
ORDER=['seller','product_listing','customer_order','order_line','fulfillment','customer_review','dispute','commission_rule','payout','payout_line','seller_status_history','fulfillment_event','payout_event','ground_truth']
def main():
 p=argparse.ArgumentParser(); p.add_argument('--input',default='data/generated'); a=p.parse_args(); folder=Path(a.input)
 init_db()
 with psycopg.connect(DATABASE_URL) as conn:
  for table in ORDER:
   path=folder/f'{table}.csv'
   if not path.exists(): continue
   with path.open('r',encoding='utf-8',newline='') as f:
    reader=csv.reader(f); cols=next(reader)
    with conn.cursor().copy(f"COPY {table} ({','.join(cols)}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)") as copy:
     copy.write(path.read_text(encoding='utf-8'))
   print(f'Loaded {table}: {sum(1 for _ in path.open(encoding="utf-8"))-1:,} rows')
 print('PostgreSQL load complete.')
if __name__=='__main__': main()
