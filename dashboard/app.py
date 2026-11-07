import os, pandas as pd, streamlit as st, psycopg, plotly.express as px
from dotenv import load_dotenv
load_dotenv(); URL=os.getenv('DATABASE_URL','postgresql://postgres:postgres@localhost:5432/yottaflex')
st.set_page_config(page_title='YottaFlex Seller Operations',layout='wide')
st.title('Seller Operations & Payout Intelligence')
st.caption('Synthetic marketplace operations monitoring | PostgreSQL source of truth')
try:
    with psycopg.connect(URL) as c:
        metrics=pd.read_sql("SELECT (SELECT count(*) FROM seller) sellers,(SELECT count(*) FROM product_listing) listings,(SELECT count(*) FROM customer_order) orders,(SELECT count(*) FROM dispute) disputes,(SELECT count(*) FROM payout) payouts,(SELECT coalesce(sum(payout_total),0) FROM payout) payout_value",c)
        m=metrics.iloc[0]; cols=st.columns(6)
        for col,label,key in zip(cols,['Sellers','Listings','Orders','Disputes','Payout batches','Payout value'],['sellers','listings','orders','disputes','payouts','payout_value']): col.metric(label,f"{m[key]:,.0f}")
        a,b=st.columns(2)
        sellers=pd.read_sql("SELECT seller_status,count(*) count FROM seller GROUP BY seller_status",c)
        a.plotly_chart(px.pie(sellers,names='seller_status',values='count',title='Seller status distribution'),use_container_width=True)
        disputes=pd.read_sql("SELECT dispute_status,count(*) count FROM dispute GROUP BY dispute_status",c)
        b.plotly_chart(px.bar(disputes,x='dispute_status',y='count',title='Disputes by status'),use_container_width=True)
        st.subheader('Policy exceptions')
        exceptions=pd.read_sql("SELECT l.listing_id,s.seller_id,s.seller_status,l.listing_status FROM product_listing l JOIN seller s USING(seller_id) WHERE s.seller_status='SUSPENDED' AND l.listing_status='ACTIVE' LIMIT 500",c)
        st.dataframe(exceptions,use_container_width=True)
        st.subheader('Recent payout reconciliation')
        rec=pd.read_sql("SELECT p.payout_id,p.payout_total,coalesce(sum(pl.net_amount),0) line_total,p.payout_total-coalesce(sum(pl.net_amount),0) difference FROM payout p LEFT JOIN payout_line pl USING(payout_id) GROUP BY p.payout_id ORDER BY p.payout_id DESC LIMIT 100",c)
        st.dataframe(rec,use_container_width=True)
except Exception as e: st.error(f'Cannot connect to PostgreSQL: {e}. Start the database and load generated data first.')
