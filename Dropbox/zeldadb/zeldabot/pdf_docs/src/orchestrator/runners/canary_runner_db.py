
#!/usr/bin/env python3
import os, json, argparse, random, sys, shutil, subprocess
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.db import fetch_docs, latest_extraction

def export_sample(filter_sql, out_root, sample):
    tmp = Path(out_root) / "pred_sample"
    if tmp.exists(): shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    rows = fetch_docs(filter_sql=filter_sql, limit=100000, offset=0)
    random.shuffle(rows)
    rows = rows[:sample]
    for r in rows:
        last = latest_extraction(r["id"])
        if not last or last.get("status") != "DONE": continue
        stem = r["stem"] or str(r["id"])
        d = tmp / stem; d.mkdir(parents=True, exist_ok=True)
        (d / "final_extraction.json").write_text(json.dumps(last.get("final_json") or {}, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(tmp)

def main():
    ap=argparse.ArgumentParser(description='Canary (DB-backed)')
    ap.add_argument('--filter', default='processed is false')
    ap.add_argument('--gold-root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--sample', type=int, default=300)
    ap.add_argument('--coverage-thresh', type=float, default=95.0)
    ap.add_argument('--accuracy-thresh', type=float, default=95.0)
    args=ap.parse_args()

    Path(args.out).mkdir(parents=True, exist_ok=True)
    pred_root = export_sample(args.filter, args.out, args.sample)
    metrics_dir = os.path.join(args.out, "metrics")
    subprocess.check_call(['python','src/qa/score_final_vs_golden.py','--pred-root',pred_root,'--gold-root',args.gold_root,'--out',metrics_dir])

    summary = json.load(open(os.path.join(metrics_dir,'metrics_summary.json'),'r',encoding='utf-8'))
    ok = summary['coverage_pct']>=args.coverage_thresh and summary['accuracy_pct']>=args.accuracy_thresh
    open(os.path.join(args.out,'report.md'),'w',encoding='utf-8').write(f"# Canary\nCoverage: {summary['coverage_pct']}%\nAccuracy: {summary['accuracy_pct']}%\n")
    if not ok: raise SystemExit('❌ Canary failed thresholds.')
    print('✅ Canary passed.')

if __name__=='__main__': main()
