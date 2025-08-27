
#!/usr/bin/env python3
import os, json, argparse, tempfile, sys, shutil, subprocess
from pathlib import Path
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.db import fetch_docs, latest_extraction

def export_db_preds(filter_sql, out_root):
    tmp = Path(out_root) / "pred_export"
    if tmp.exists(): shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    rows = fetch_docs(filter_sql=filter_sql, limit=100000, offset=0)
    for r in rows:
        last = latest_extraction(r["id"])
        if not last or last.get("status") != "DONE": continue
        stem = r["stem"] or str(r["id"])
        d = tmp / stem; d.mkdir(parents=True, exist_ok=True)
        (d / "final_extraction.json").write_text(json.dumps(last.get("final_json") or {}, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(tmp)

def main():
    load_dotenv()
    ap=argparse.ArgumentParser(description='Golden scorer (DB-backed)')
    ap.add_argument('--filter', default='training_set = true')
    ap.add_argument('--gold-root', required=True)
    ap.add_argument('--prompts', required=True)  # kept for parity
    ap.add_argument('--out', required=True)
    ap.add_argument('--coverage-thresh', type=float, default=95.0)
    ap.add_argument('--accuracy-thresh', type=float, default=95.0)
    ap.add_argument('--max-field-regression', type=float, default=1.0)
    args=ap.parse_args()

    Path(args.out).mkdir(parents=True, exist_ok=True)
    pred_root = export_db_preds(args.filter, args.out)
    metrics_dir = os.path.join(args.out, "metrics")
    subprocess.check_call(['python','src/qa/score_final_vs_golden.py','--pred-root',pred_root,'--gold-root',args.gold_root,'--out',metrics_dir])

    summary = json.load(open(os.path.join(metrics_dir,'metrics_summary.json'),'r',encoding='utf-8'))
    base_dir='metrics/baselines'; Path(base_dir).mkdir(parents=True, exist_ok=True)
    base_path=os.path.join(base_dir,'latest.json'); baseline=json.load(open(base_path,'r',encoding='utf-8')) if os.path.exists(base_path) else None

    gate={'coverage_ok': summary['coverage_pct']>=args.coverage_thresh, 'accuracy_ok': summary['accuracy_pct']>=args.accuracy_thresh}
    regression_ok=True
    if baseline:
        regression_ok = (baseline['accuracy_pct'] - summary['accuracy_pct']) <= args.max_field_regression
    gate['regression_ok']=regression_ok
    open(os.path.join(args.out,'report.md'),'w',encoding='utf-8').write(json.dumps({'summary':summary,'gate':gate,'baseline':baseline}, indent=2))

    if not baseline or (summary['accuracy_pct']>baseline['accuracy_pct']) or (summary['coverage_pct']>baseline['coverage_pct']):
        open(base_path,'w',encoding='utf-8').write(json.dumps(summary,indent=2))

    if not (gate['coverage_ok'] and gate['accuracy_ok'] and gate['regression_ok']):
        raise SystemExit('❌ Golden gate failed.')
    print('✅ Golden gate passed.')

if __name__=='__main__': main()
