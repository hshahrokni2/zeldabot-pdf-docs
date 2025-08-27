
#!/usr/bin/env python3
import os, json, argparse, copy
DIRECTIVES = """You are an information extraction model. Follow STRICTLY:
1) Respond ONLY with a SINGLE minified JSON object. No prose, no markdown.
2) Currency is SEK. Amounts MUST be numeric (no spaces/units). Use integers when possible.
3) Percentages MUST be numbers (e.g., 3.79) with no '%'. 
4) Dates MUST be ISO YYYY-MM-DD.
5) Use null if missing. Do NOT invent.
6) Preserve EXACT key names from example JSON. No extra keys.
7) Reconstruct wrapped item names.
8) No comments/explanations.
"""
def split_prompt(text):
    last_json=None; last_span=None; opens=[i for i,ch in enumerate(text) if ch=='{']; closes=[i for i,ch in enumerate(text) if ch=='}']
    for i in opens:
        for j in reversed(closes):
            if j>i:
                cand=text[i:j+1]
                try: obj=json.loads(cand); last_json=cand; last_span=(i,j+1); break
                except: pass
        if last_json: break
    if last_json and last_span: return (text[:last_span[0]].strip(), last_json.strip())
    return (text,None)
def main():
    ap=argparse.ArgumentParser(description='Normalize prompts (rule-based)')
    ap.add_argument('--prompts',required=True); ap.add_argument('--apply',action='store_true'); ap.add_argument('--dry-run',action='store_true')
    a=ap.parse_args(); repo=json.load(open(a.prompts,'r',encoding='utf-8'))
    updated=copy.deepcopy(repo); changes={}
    for k,v in repo.items():
        body,ex=split_prompt(v); new_body=body if 'SINGLE minified JSON' in body else DIRECTIVES+'\n\n'+(body or '')
        new_text=new_body + ('\n'+ex if ex else '')
        if new_text!=v: updated[k]=new_text; changes[k]=(v[:400], new_text[:400])
    if a.dry_run or not a.apply:
        print('=== Proposed prompt updates ==='); 
        if not changes: print('No changes proposed.')
        else:
            for k,(b,af) in changes.items(): print(f'\n--- {k} ---\nBEFORE:\n{b}\n\nAFTER:\n{af}')
        return
    open(a.prompts+'.bak','w',encoding='utf-8').write(json.dumps(repo,ensure_ascii=False,indent=2))
    open(a.prompts,'w',encoding='utf-8').write(json.dumps(updated,ensure_ascii=False,indent=2))
    print('✅ Prompts updated. Backup saved.')
if __name__=='__main__': main()
