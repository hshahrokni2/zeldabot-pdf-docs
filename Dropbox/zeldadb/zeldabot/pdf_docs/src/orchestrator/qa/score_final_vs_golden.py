
#!/usr/bin/env python3
import os, json, argparse, glob, csv
def norm_str(x):
    if x is None: return None
    if not isinstance(x, str): return x
    return ' '.join(x.strip().split()).lower()
def num_close(a, b, abs_tol=1.0, rel_tol=0.005):
    try: a=float(a); b=float(b)
    except: return False
    if abs(a-b) <= abs_tol: return True
    denom=max(abs(a),abs(b),1.0); return abs(a-b)/denom <= rel_tol
def eq(a,b):
    if isinstance(a,(int,float)) or isinstance(b,(int,float)): return num_close(a,b)
    if isinstance(a,str) or isinstance(b,str): return norm_str(a)==norm_str(b)
    return a==b
def compare_json(pred,gold):
    if isinstance(gold,dict) and isinstance(pred,dict):
        t=c=0; keys=set(gold.keys())|set(pred.keys())
        for k in keys:
            tt,cc=compare_json(pred.get(k), gold.get(k)); t+=tt; c+=cc
        return t,c
    if isinstance(gold,list) and isinstance(pred,list):
        t=c=0
        for i in range(max(len(gold),len(pred))):
            g=gold[i] if i<len(gold) else None; p=pred[i] if i<len(pred) else None
            tt,cc=compare_json(p,g); t+=tt; c+=cc
        return t,c
    return 1, 1 if eq(pred,gold) else 0
def main():
    ap=argparse.ArgumentParser(description='Score outputs vs. goldens')
    ap.add_argument('--pred-root',required=True); ap.add_argument('--gold-root',required=True); ap.add_argument('--out',required=True)
    ap.add_argument('--require-sections',nargs='*',default=[])
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True)
    preds={}
    for p in glob.glob(os.path.join(a.pred_root,'*','final_extraction.json')):
        stem=os.path.basename(os.path.dirname(p)); preds[stem]=json.load(open(p,'r',encoding='utf-8'))
    golds={}
    for p in glob.glob(os.path.join(a.gold_root,'*.json')):
        stem=os.path.splitext(os.path.basename(p))[0]; golds[stem]=json.load(open(p,'r',encoding='utf-8'))
    details=[]; covered=0; universe=golds.keys() or preds.keys()
    for stem in universe:
        pred=preds.get(stem); cov = pred is not None and (all(k in pred for k in a.require_sections) if a.require_sections else True)
        covered+=1 if cov else 0
        if pred is not None and stem in golds:
            t,c=compare_json(pred,golds[stem]); acc=round((c/max(t,1))*100,2); details.append([stem,'1' if cov else '0',t,c,acc])
        else:
            details.append([stem,'1' if cov else '0',0,0,0.0])
    coverage=round((covered/max(len(universe),1))*100.0,2)
    total=sum(int(r[2]) for r in details); correct=sum(int(r[3]) for r in details)
    accuracy=round((correct/max(total,1))*100.0,2)
    json.dump({'docs_total':len(universe),'coverage_pct':coverage,'accuracy_pct':accuracy,'covered_docs':covered,'fields_total':total,'fields_correct':correct}, open(os.path.join(a.out,'metrics_summary.json'),'w',encoding='utf-8'), indent=2)
    with open(os.path.join(a.out,'metrics_detail.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['stem','covered','total_fields','correct_fields','doc_accuracy_pct']); [w.writerow(r) for r in details]
    print(f'✅ Wrote metrics to {a.out}'); print(f'Coverage: {coverage}% | Accuracy: {accuracy}%')
if __name__=='__main__': main()
