
#!/usr/bin/env python3
import os, json, argparse
REQUIRED='Respond ONLY with a SINGLE minified JSON object'
def last_json(text):
    opens=[i for i,ch in enumerate(text) if ch=='{']; closes=[i for i,ch in enumerate(text) if ch=='}']
    best=None
    for i in opens:
        for j in reversed(closes):
            if j>i:
                cand=text[i:j+1]
                try: json.loads(cand); best=cand; break
                except: pass
        if best: break
    return best
def main():
    ap=argparse.ArgumentParser(description='Prompt linter')
    ap.add_argument('--prompts',required=True); a=ap.parse_args()
    repo=json.load(open(a.prompts,'r',encoding='utf-8')); errs=0
    for k,v in repo.items():
        if REQUIRED not in v or last_json(v) is None:
            errs+=1; print(f'❌ {k}: missing required directive or JSON example not parseable')
    print('✅ All prompts passed.' if errs==0 else f'❌ {errs} prompt(s) need attention.')
if __name__=='__main__': main()
