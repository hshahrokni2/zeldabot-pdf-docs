
import os, base64, json, requests
GEMINI_API_KEY=os.getenv('GEMINI_API_KEY','')
GEMINI_MODEL=os.getenv('GEMINI_MODEL','gemini-1.5-pro')
STRICT_SINGLE=os.getenv('GEMINI_STRICT_SINGLE_PAGE','1')=='1'
API='https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
INSTRUCT='''You are a careful manual reviewer. Evaluate ONLY the MAIN page image.
Use the PREV and NEXT page images ONLY for orientation/context.
Return a SINGLE minified JSON with keys:
{"verdict":"agree|disagree|unsure","notes":"<short reason>","suggested_corrections":{}}
If you disagree, include minimal suggested_corrections as a valid JSON diff for the fields in question.
Do not include any prose outside the JSON.
'''
def b64img(jpeg_bytes): return base64.b64encode(jpeg_bytes).decode('utf-8')
def call_gemini(main_bytes, prev_bytes=None, next_bytes=None, target_json=None):
    if not GEMINI_API_KEY: raise RuntimeError('GEMINI_API_KEY is not set.')
    parts=[{"role":"user","parts":[{"text":INSTRUCT}]}]
    imgs=[]
    if prev_bytes is not None: imgs.append({"inline_data":{"mime_type":"image/jpeg","data":b64img(prev_bytes)}})
    imgs.append({"inline_data":{"mime_type":"image/jpeg","data":b64img(main_bytes)}})
    if next_bytes is not None: imgs.append({"inline_data":{"mime_type":"image/jpeg","data":b64img(next_bytes)}})
    if STRICT_SINGLE and len(imgs)>3: imgs=imgs[:3]
    parts.append({"role":"user","parts": imgs + ([{"text":json.dumps(target_json)}] if target_json else [])})
    payload={"contents": parts, "generationConfig": {"temperature": 0.0, "maxOutputTokens": 512}}
    url=API.format(model=GEMINI_MODEL, key=GEMINI_API_KEY)
    r=requests.post(url,json=payload,timeout=60); r.raise_for_status(); data=r.json()
    text=''
    try: text=data['candidates'][0]['content']['parts'][0]['text']
    except Exception: return {"verdict":"unsure","notes":"No text in response","suggested_corrections":{}}
    s=text.find('{'); e=text.rfind('}')
    if s!=-1 and e!=-1 and e>s:
        try: return json.loads(text[s:e+1])
        except: return {"verdict":"unsure","notes":"Non-JSON output","suggested_corrections":{}}
    return {"verdict":"unsure","notes":"No JSON found","suggested_corrections":{}}
