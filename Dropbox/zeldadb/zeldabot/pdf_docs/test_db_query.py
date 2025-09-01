import psycopg2
import os

os.environ["DATABASE_URL"] = "postgresql://postgres:h100pass@localhost:15432/zelda_arsredovisning"

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cursor = conn.cursor()

cursor.execute("""
    SELECT id, filename, LENGTH(pdf_binary) as pdf_size
    FROM arsredovisning_documents
    WHERE pdf_binary IS NOT NULL
    ORDER BY created_at DESC
    LIMIT 1
""")

rows = cursor.fetchall()
print(f"Found {len(rows)} documents")
for row in rows:
    print(f"ID: {row[0]}, Filename: {row[1]}, PDF Size: {row[2]} bytes")

conn.close()
