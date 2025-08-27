
#!/usr/bin/env python3
import json, argparse, os
from jsonschema import Draft202012Validator
SCHEMA_PATH=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'schemas','final_extraction.schema.json')
def main():
    p=argparse.ArgumentParser(description='Validate final_extraction.json against schema')
    p.add_argument('--final',required=True); p.add_argument('--schema',default=SCHEMA_PATH)
    a=p.parse_args(); schema=json.load(open(a.schema,'r',encoding='utf-8')); data=json.load(open(a.final,'r',encoding='utf-8'))
    v=Draft202012Validator(schema); errs=sorted(v.iter_errors(data), key=lambda e: e.path)
    if errs:
        print('❌ Validation errors:')
        for e in errs:
            path='/'.join(str(x) for x in e.path) or '<root>'; print(f'- {path}: {e.message}'); exit(1)
    print('✅ Validation passed.')
if __name__=='__main__': main()
