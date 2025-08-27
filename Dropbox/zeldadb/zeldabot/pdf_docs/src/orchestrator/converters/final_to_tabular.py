
#!/usr/bin/env python3
import os, json, argparse, csv, pathlib
def write_csv(path, header, rows):
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(header); [w.writerow(r) for r in rows]
def main():
    ap=argparse.ArgumentParser(description='Convert final_extraction.json to CSV tables')
    ap.add_argument('--final',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    d=json.load(open(a.final,'r',encoding='utf-8')); os.makedirs(a.out, exist_ok=True)
    if 'financial_statement' in d:
        items=d['financial_statement'].get('items',[]); rows=[(i.get('item'),i.get('note'),i.get('current_year'),i.get('previous_year')) for i in items]
        write_csv(os.path.join(a.out,'financial_statement.csv'), ['item','note','current_year','previous_year'], rows)
    if 'multi_year_overview' in d:
        headers=d['multi_year_overview'].get('headers',[]); rows=d['multi_year_overview'].get('rows',[])
        out_rows=[[r.get(h) if isinstance(r,dict) else '' for h in headers] for r in rows]
        write_csv(os.path.join(a.out,'multi_year_overview.csv'), headers, out_rows)
    if 'revenue_breakdown' in d:
        rows=[(i.get('item'),i.get('current_year'),i.get('previous_year')) for i in d['revenue_breakdown'].get('items',[])]
        write_csv(os.path.join(a.out,'revenue_breakdown.csv'), ['item','current_year','previous_year'], rows)
    if 'cost_breakdown' in d:
        title=d['cost_breakdown'].get('note_title'); rows=[(title,i.get('item'),i.get('current_year'),i.get('previous_year')) for i in d['cost_breakdown'].get('items',[])]
        write_csv(os.path.join(a.out,'cost_breakdown.csv'), ['note_title','item','current_year','previous_year'], rows)
    if 'asset_depreciation' in d:
        rows=[(d['asset_depreciation'].get('asset_type'),i.get('group'),i.get('item'),i.get('value')) for i in d['asset_depreciation'].get('items',[])]
        write_csv(os.path.join(a.out,'asset_depreciation.csv'), ['asset_type','group','item','value'], rows)
    if 'financial_loans' in d:
        rows=[(i.get('lender'),i.get('amount'),i.get('interest_rate'),i.get('maturity_date')) for i in d.get('financial_loans',[])]
        write_csv(os.path.join(a.out,'financial_loans.csv'), ['lender','amount','interest_rate','maturity_date'], rows)
    if 'pledged_assets' in d:
        rows=[(i.get('item'),i.get('amount_current_year'),i.get('amount_previous_year')) for i in d.get('pledged_assets',[])]
        write_csv(os.path.join(a.out,'pledged_assets.csv'), ['item','amount_current_year','amount_previous_year'], rows)
    print(f'✅ CSVs written to {a.out}')
if __name__=='__main__': main()
