
import os, json, psycopg2, psycopg2.extras, contextlib

DSN = dict(
    host=os.getenv("PGHOST","127.0.0.1"),
    port=os.getenv("PGPORT","5432"),
    dbname=os.getenv("PGDATABASE","postgres"),
    user=os.getenv("PGUSER","postgres"),
    password=os.getenv("PGPASSWORD",""),
    sslmode=os.getenv("PGSSLMODE","prefer")
)

@contextlib.contextmanager
def get_conn():
    conn = psycopg2.connect(**DSN)
    try:
        yield conn
    finally:
        conn.close()

def fetch_docs(filter_sql="training_set = true", limit=100, offset=0):
    sql = f"SELECT id, stem, pdf_bytes FROM documents WHERE {filter_sql} ORDER BY id LIMIT %s OFFSET %s"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, (limit, offset))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

def store_extraction(document_id, section_map, final_json, status="DONE", message="", prompt_hash=None, dpi=None):
    sql = """INSERT INTO extractions (document_id, section_map, final_json, status, message, prompt_hash, dpi)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (str(document_id), json.dumps(section_map), json.dumps(final_json), status, message, prompt_hash, dpi))
            conn.commit()

def latest_extraction(document_id):
    sql = "SELECT * FROM extractions WHERE document_id = %s ORDER BY created_at DESC LIMIT 1"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, (str(document_id),))
            row = cur.fetchone()
            return dict(row) if row else None

def insert_review(document_id, page_number, verdict, notes, suggested_corrections, reviewer="gemini"):
    sql = """INSERT INTO review_findings (document_id, page_number, verdict, notes, suggested_corrections, reviewer)
             VALUES (%s, %s, %s, %s, %s, %s)"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (str(document_id), page_number, verdict, notes, json.dumps(suggested_corrections) if suggested_corrections else None, reviewer))
            conn.commit()

def enqueue_hitl(document_id, page_number, reason, payload):
    sql = """INSERT INTO hitl_queue (document_id, page_number, reason, payload) VALUES (%s, %s, %s, %s)"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (str(document_id), page_number, reason, json.dumps(payload)))
            conn.commit()

def add_learning(lesson_type, pattern, action, source_review_id=None):
    sql = """INSERT INTO learning_memory (lesson_type, pattern, action, source_review_id) VALUES (%s, %s, %s, %s)"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (lesson_type, json.dumps(pattern), json.dumps(action), str(source_review_id) if source_review_id else None))
            conn.commit()

def fetch_learnings():
    sql = "SELECT lesson_type, pattern, action FROM learning_memory WHERE active = true ORDER BY created_at DESC"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]
