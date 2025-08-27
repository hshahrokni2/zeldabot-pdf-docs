
#!/usr/bin/env python3
import os, json, argparse, sys, fitz
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.db import fetch_docs, latest_extraction, insert_review, enqueue_hitl, add_learning, get_conn
from reviewer.reviewer_gemini import call_gemini

def pick_page(doc, hint: str):
    hint = (hint or "").lower()
    for i in range(len(doc)):
        t = (doc[i].get_text("text") or "").lower()
        if hint and hint in t:
            return i
    return max(0, (len(doc)//2)-1)

def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Gemini reviewer (batch)")
    ap.add_argument("--filter", default="training_set = true")
    ap.add_argument("--auto-apply", action="store_true")
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()

    rows = fetch_docs(filter_sql=args.filter, limit=args.limit, offset=0)
    for r in rows:
        last = latest_extraction(r["id"])
        if not last or last.get("status") != "DONE":
            continue
        final = last.get("final_json") or {}
        missing = [k for k in ["financial_loans","asset_depreciation","pledged_assets","revenue_breakdown","cost_breakdown"] if k not in final]
        if not missing:
            continue
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pdf_bytes FROM documents WHERE id = %s", (str(r["id"]),))
                pdf_bytes = cur.fetchone()[0]
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for section in missing:
            hint = {
                "financial_loans": "skulder till kreditinstitut",
                "asset_depreciation": "byggnad och mark",
                "pledged_assets": "ställda säkerheter",
                "revenue_breakdown": "nettoomsättning",
                "cost_breakdown": "kostnader"
            }.get(section, "")
            idx = pick_page(doc, hint)
            prev_b = doc[idx-1].get_pixmap(dpi=200).tobytes("jpeg") if idx-1 >= 0 else None
            main_b = doc[idx].get_pixmap(dpi=200).tobytes("jpeg")
            next_b = doc[idx+1].get_pixmap(dpi=200).tobytes("jpeg") if idx+1 < len(doc) else None
            target = {section: final.get(section)}
            res = call_gemini(main_b, prev_b, next_b, target_json=target)
            insert_review(r["id"], idx+1, res.get("verdict","unsure"), res.get("notes",""), res.get("suggested_corrections"))
            if res.get("verdict") in ("unsure",) and not args.auto_apply:
                enqueue_hitl(r["id"], idx+1, f"Gemini {res.get('verdict')}", {"section": section, "hint": hint})
            if args.auto_apply and res.get("verdict")=="disagree" and res.get("suggested_corrections"):
                add_learning("postprocess_rule", {"section": section}, {"apply": res["suggested_corrections"]})
    print("✅ Gemini batch review completed.")

if __name__ == "__main__":
    main()
