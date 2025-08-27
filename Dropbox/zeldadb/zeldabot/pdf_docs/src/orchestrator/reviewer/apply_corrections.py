
#!/usr/bin/env python3
import os, json, argparse, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.db import latest_extraction, add_learning, get_conn

def deep_merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        res = dict(a)
        for k,v in b.items():
            res[k] = deep_merge(res.get(k), v)
        return res
    return b if b is not None else a

def main():
    ap = argparse.ArgumentParser(description="Apply Gemini-suggested corrections into extractions")
    ap.add_argument("--filter", default="training_set = true")
    args = ap.parse_args()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, document_id, suggested_corrections FROM review_findings WHERE suggested_corrections IS NOT NULL")
            rows = cur.fetchall()

    applied = 0
    for rid, doc_id, corr in rows:
        last = latest_extraction(doc_id)
        if not last or last.get("status") != "DONE":
            continue
        final = last.get("final_json") or {}
        try:
            corrected = deep_merge(final, corr)
        except Exception:
            continue
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO extractions (document_id, section_map, final_json, status, message, prompt_hash, dpi)
                               VALUES (%s, %s, %s, %s, %s, %s, %s)""" ,
                            (str(doc_id), json.dumps(last.get("section_map") or {}), json.dumps(corrected), "DONE", "corrected_by_gemini", last.get("prompt_hash"), last.get("dpi")))
                conn.commit()
        add_learning("postprocess_rule", {"from_review": str(rid)}, {"applied": True})
        applied += 1
    print(f"✅ Applied {applied} correction(s).")

if __name__ == "__main__":
    main()
