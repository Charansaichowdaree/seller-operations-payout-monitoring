import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL=os.getenv('DATABASE_URL','postgresql://postgres:postgres@localhost:5432/yottaflex')
def connect(): return psycopg.connect(DATABASE_URL, row_factory=dict_row)
def init_db():
    sql=(Path(__file__).resolve().parents[1]/'sql'/'schema.sql').read_text(encoding='utf-8')
    with connect() as conn: conn.execute(sql)
