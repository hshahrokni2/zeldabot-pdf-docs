
#!/usr/bin/env python3
import os, argparse, requests, json
def main():
    ap=argparse.ArgumentParser(description='Ping QWEN endpoint for readiness')
    ap.add_argument('--api-url', default=os.getenv('QWEN_VL_API_URL','http://127.0.0.1:5000/v1/chat/completions'))
    a=ap.parse_args()
    payload={'model':'qwen-vl-chat','messages':[{'role':'user','content':[{'type':'text','text':'{}'}]}],'max_tokens':8}
    try:
        r=requests.post(a.api_url,json=payload,timeout=10); r.raise_for_status()
        data=r.json(); print(json.dumps({'ok': 'choices' in data, 'response_keys': list(data.keys())}, indent=2))
    except Exception as e:
        print(json.dumps({'ok': False, 'error': str(e)}))
if __name__=='__main__': main()
