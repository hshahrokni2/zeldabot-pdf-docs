
#!/usr/bin/env python3
import os, json, logging, base64, re
from typing import List, Dict, Any, Optional
import fitz, requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SectionizerAgent')

QWEN_VL_API_URL = os.getenv('QWEN_VL_API_URL', f"{os.getenv('OLLAMA_URL','http://127.0.0.1:11434')}/v1/chat/completions")
SECTIONIZER_MODE = os.getenv('SECTIONIZER_MODE', 'heuristic').strip().lower()

def _sectionizer_system_prompt() -> str:
    return """
You are an expert document analyst AI. Your single task is to classify a page image from a Swedish BRF annual report by matching it to the closest concept in a canonical list.
Respond ONLY with: {"section_name":"<name>","page_number":<num>,"confidence":<0-1>}
Canonical: cover_page, table_of_contents, management_report, income_statement, balance_sheet, cash_flow_statement,
changes_in_equity, multi_year_overview, notes, signatures, auditors_report, other
"""

class SectionizerAgent:
    def __init__(self, pdf_path: str, mode: Optional[str] = None):
        self.pdf_path = pdf_path
        self.mode = (mode or SECTIONIZER_MODE).lower()
        self.headers = {'Content-Type': 'application/json'}

    @staticmethod
    def _heuristic_classify_page_text(text: str, page_number: int) -> Dict[str, Any]:
        t = (text or '').lower()
        def has_any(words): return any(w in t for w in words)
        # Debug: print first 200 chars if nothing matches
        debug_mode = os.getenv('SECTIONIZER_DEBUG', '0') == '1'
        if debug_mode and page_number <= 3:
            print(f"=== PAGE {page_number} TEXT DEBUG ===")
            print(repr(t[:200]))
            print()
        
        if page_number == 1 and has_any(['årsredovisning','årsberättelse','brf','bostadsrättsförening']):
            return {'section_name':'cover_page','page_number':page_number,'confidence':0.75}
        if has_any(['innehållsförteckning','innehåll','contents']):
            return {'section_name':'table_of_contents','page_number':page_number,'confidence':0.9}
        if has_any(['förvaltningsberättelse','förvaltningsrapport','verksamhetsberättelse']):
            return {'section_name':'management_report','page_number':page_number,'confidence':0.95}
        if has_any(['resultaträkning','resultat','intäkter och kostnader','rörelsens intäkter']):
            return {'section_name':'income_statement','page_number':page_number,'confidence':0.95}
        if has_any(['balansräkning','balans','tillgångar','skulder och eget kapital','anläggningstillgångar']):
            return {'section_name':'balance_sheet','page_number':page_number,'confidence':0.95}
        if has_any(['kassaflödesanalys']):
            return {'section_name':'cash_flow_statement','page_number':page_number,'confidence':0.95}
        if has_any(['förändringar i eget kapital','förändring i eget kapital']):
            return {'section_name':'changes_in_equity','page_number':page_number,'confidence':0.95}
        if has_any(['flerårsöversikt','flera års översikt','flerårs-']):
            return {'section_name':'multi_year_overview','page_number':page_number,'confidence':0.95}
        if has_any(['noter']) or re.search(r'(^|\n)\s*not\s*\d+', t):
            return {'section_name':'notes','page_number':page_number,'confidence':0.85}
        if has_any(['underskrifter','undertecknat','på styrelsens vägnar']):
            return {'section_name':'signatures','page_number':page_number,'confidence':0.75}
        if has_any(['revisionsberättelse']):
            return {'section_name':'auditors_report','page_number':page_number,'confidence':0.95}
        return {'section_name':'other','page_number':page_number,'confidence':0.5}

    def _call_qwen_vl_api(self, page_image_base64: str, page_number: int) -> Dict[str, Any]:
        model_name = os.getenv('QWEN_MODEL_TAG', 'qwen2.5vl:7b')
        payload = {'model':model_name,'messages':[
            {'role':'system','content':_sectionizer_system_prompt()},
            {'role':'user','content':[{'type':'text','text':f'Analyze page number {page_number}.'},
                                      {'type':'image_url','image_url':{'url':f'data:image/jpeg;base64,{page_image_base64}'}}]}],
            'max_tokens':150,'temperature':0.0}
        try:
            r = requests.post(QWEN_VL_API_URL, headers=self.headers, json=payload, timeout=90)
            r.raise_for_status()
            content = r.json()['choices'][0]['message']['content']
            # Strip markdown code fences if present (handle text before fence)
            if '```json' in content:
                import re
                match = re.search(r'```(?:json)?\s*\n(.*?)\n```', content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
            elif content.strip().startswith('```'):
                lines = content.strip().split('\n')
                if len(lines) >= 3 and lines[0].startswith('```') and lines[-1] == '```':
                    content = '\n'.join(lines[1:-1])
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f'LLM classification failed on page {page_number}: {e}')
            return {'section_name':'other','page_number':page_number,'confidence':0.0}

    def analyze_document(self) -> Dict[str, Any]:
        doc = fitz.open(self.pdf_path); classifications=[]
        for i, page in enumerate(doc, start=1):
            if self.mode=='llm':
                b64 = base64.b64encode(page.get_pixmap(dpi=150).tobytes('jpeg')).decode('utf-8')
                item = self._call_qwen_vl_api(b64, i)
            else:
                item = self._heuristic_classify_page_text(page.get_text('text'), i)
            classifications.append(item)
        doc.close(); return self._aggregate_classifications(classifications)

    @staticmethod
    def _aggregate_classifications(classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not classifications: return {}
        final_map={}; cur=None; start=None
        for it in sorted(classifications, key=lambda x: x['page_number']):
            sec=it.get('section_name','other'); num=it.get('page_number')
            if cur is None: cur=sec; start=num; continue
            if sec!=cur:
                final_map[f'{cur}_{start}']={'start_page':start,'end_page':num-1,'canonical_name':cur}
                cur=sec; start=num
        if cur is not None and start is not None:
            last=sorted(classifications,key=lambda x:x['page_number'])[-1]['page_number']
            final_map[f'{cur}_{start}']={'start_page':start,'end_page':last,'canonical_name':cur}
        return final_map

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--pdf',required=True); p.add_argument('--out',default='section_map.json')
    p.add_argument('--mode',choices=['heuristic','llm'],default=os.getenv('SECTIONIZER_MODE','heuristic'))
    a=p.parse_args()
    m=SectionizerAgent(a.pdf,mode=a.mode).analyze_document()
    open(a.out,'w',encoding='utf-8').write(json.dumps(m,ensure_ascii=False,indent=2))
    print(f'✅ Section map saved to {a.out}')
