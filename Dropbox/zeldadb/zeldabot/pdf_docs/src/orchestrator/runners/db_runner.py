
#!/usr/bin/env python3
import os, json, argparse, asyncio, tempfile, time, hashlib, sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.db import fetch_docs, store_extraction, fetch_learnings
from agent_sectionizer import SectionizerAgent
from agent_orchestrator import OrchestratorAgent

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def merge_missing_only(dst, patch):
    if isinstance(dst, dict) and isinstance(patch, dict):
        out=dict(dst)
        for k,v in patch.items():
            if k not in out or out[k] in (None, [], {}, ""):
                out[k]=v
            elif isinstance(out[k], dict) and isinstance(v, dict):
                out[k]=merge_missing_only(out[k], v)
        return out
    return dst

def apply_learnings(final_json, learnings):
    out=dict(final_json or {})
    for L in learnings:
        if L.get("lesson_type")=="postprocess_rule":
            patt=L.get("pattern") or {}
            action=L.get("action") or {}
            section=(patt.get("section") if isinstance(patt, dict) else None)
            apply_obj=(action.get("apply") if isinstance(action, dict) else None)
            if section and apply_obj and (section not in out or not out.get(section)):
                out = merge_missing_only(out, apply_obj)
    return out

async def process_doc(row, tmpdir, prompts_path, sectionizer_mode, dpi, learnings):
    did, stem, pdf_bytes = row["id"], row["stem"], row["pdf_bytes"]
    pdf_path = os.path.join(tmpdir, f"{stem or did}.pdf")
    with open(pdf_path, "wb") as f: f.write(pdf_bytes)
    sectionizer = SectionizerAgent(pdf_path, mode=sectionizer_mode)
    section_map = sectionizer.analyze_document()
    os.environ["ORCH_DPI"] = str(dpi)
    prompts = json.load(open(prompts_path, "r", encoding="utf-8"))
    orch = OrchestratorAgent(pdf_path, prompts=prompts)
    final = await orch.run_workflow(section_map)
    final = apply_learnings(final, learnings)
    return section_map, final

async def main_async(args):
    load_dotenv()
    rows = fetch_docs(filter_sql=args.filter, limit=args.limit, offset=args.offset)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix="db_runner_")
    prompt_hash = sha256_file(args.prompts)
    learnings = fetch_learnings()
    start = time.time(); done = 0
    for row in rows:
        try:
            sm, fj = await process_doc(row, tmpdir, args.prompts, args.sectionizer_mode, args.dpi, learnings)
            store_extraction(row["id"], sm, fj, status="DONE", prompt_hash=prompt_hash, dpi=args.dpi)
            done += 1
            if done % 10 == 0: print(f"Processed {done}/{len(rows)}")
        except Exception as e:
            store_extraction(row["id"], {}, {}, status="FAILED", message=str(e), prompt_hash=prompt_hash, dpi=args.dpi)
            print(f"FAILED {row['id']}: {e}")
    print(f"✅ Complete. {done}/{len(rows)} processed in {round(time.time()-start,2)}s.")

def main():
    ap = argparse.ArgumentParser(description="DB-backed runner")
    ap.add_argument("--filter", default="training_set = true")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--out", default="./outputs_db")
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--sectionizer-mode", default=os.getenv("SECTIONIZER_MODE","heuristic"))
    ap.add_argument("--dpi", type=int, default=int(os.getenv("ORCH_DPI","200")))
    args = ap.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
