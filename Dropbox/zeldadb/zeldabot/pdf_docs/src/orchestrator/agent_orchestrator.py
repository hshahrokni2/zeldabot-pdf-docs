
#!/usr/bin/env python3
import os, json, logging, base64, asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import fitz, aiohttp

# Import HF sectioning improvements
from .header_postfilter import HeaderPostFilter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('OrchestratorAgent_Enhanced')

QWEN_VL_API_URL = os.getenv('QWEN_VL_API_URL', f"{os.getenv('OLLAMA_URL','http://127.0.0.1:11434')}/v1/chat/completions")
ORCH_DPI = int(os.getenv('ORCH_DPI','200'))

def load_prompts(path: str) -> Dict[str, str]:
    """Load prompts from registry.json with template file resolution"""
    with open(path,'r',encoding='utf-8') as f:
        registry = json.load(f)
    
    prompts = {}
    base_dir = Path(path).parent.parent
    
    for key, config in registry.items():
        if isinstance(config, dict) and "template_path" in config:
            template_path = base_dir / config["template_path"]
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as tf:
                    prompts[key] = tf.read()
            else:
                print(f"⚠️  Template not found: {template_path}")
                prompts[key] = f"Template missing for {key}"
        else:
            # Fallback for direct prompt content
            prompts[key] = str(config)
    
    return prompts

class OrchestratorAgent:
    def __init__(self, pdf_path: str, prompts: Dict[str, str]):
        self.pdf_path=pdf_path; self.doc=fitz.open(pdf_path); self.prompts=prompts
        
        # Initialize HF sectioning improvements
        self.post_filter = HeaderPostFilter()
        self.enable_hf_sectioning = os.getenv("ENABLE_HF_SECTIONING", "false").lower() == "true"
        
        logger.info(f"🔧 Orchestrator initialized with HF sectioning: {self.enable_hf_sectioning}")

    def _page_images_b64(self, start: int, end: int) -> List[str]:
        return [base64.b64encode(self.doc[i].get_pixmap(dpi=ORCH_DPI).tobytes('jpeg')).decode('utf-8') for i in range(start-1,end)]

    @staticmethod
    def _deep_merge(d1: Dict, d2: Dict) -> Dict:
        if not isinstance(d2, dict): return d1
        for k,v in d2.items():
            if k in d1 and isinstance(d1[k],dict) and isinstance(v,dict): d1[k]=OrchestratorAgent._deep_merge(d1[k],v)
            elif k in d1 and isinstance(d1[k],list) and isinstance(v,list): d1[k].extend(v)
            else: d1[k]=v
        return d1

    async def _dispatch(self, session: aiohttp.ClientSession, name: str, prompt: str, images: List[str]) -> Dict:
        model_name = os.getenv('QWEN_MODEL_TAG', 'qwen2.5vl:7b')
        payload={'model':model_name,'messages':[{'role':'user','content':[{'type':'text','text':prompt}] +                      [{'type':'image_url','image_url':{'url':f'data:image/jpeg;base64,{img}'}} for img in images]}],
                 'max_tokens':2048,'temperature':0.0}
        try:
            async with session.post(QWEN_VL_API_URL,json=payload,timeout=180) as resp:
                resp.raise_for_status(); content=(await resp.json())['choices'][0]['message']['content']
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
                return json.loads(content)
        except Exception as e:
            logger.error(f"Task '{name}' failed: {e}"); return {'error': f'Task {name} failed: {e}'}

    def _map_note_to_prompt_key(self, page_num: int) -> Optional[str]:
        text=self.doc[page_num-1].get_text('text').lower()
        if 'skulder till kreditinstitut' in text or 'långfristiga skulder' in text: return 'note_financial_loans'
        if 'byggnad och mark' in text or 'avskrivningar' in text or 'avskrivning' in text: return 'note_asset_depreciation'
        if 'ställda säkerheter' in text: return 'note_pledged_assets'
        if 'nettoomsättning' in text or 'rörelseintäkter' in text or 'övriga rörelseintäkter' in text: return 'note_revenue_breakdown'
        if any(k in text for k in ['kostnader','fastighetssköt','reparation','taxebundna kostnader','övriga externa kostnader','personalkostnader','räntekostnader']): return 'note_cost_breakdown'
        return None

    async def run_workflow(self, section_map: Dict[str, Any]) -> Dict:
        results={}; tasks=[]
        async with aiohttp.ClientSession() as session:
            for _, meta in section_map.items():
                start,end,name=meta['start_page'],meta['end_page'],meta['canonical_name']
                images=self._page_images_b64(start,end)
                if name=='management_report':
                    for key in ['general_property','governance','maintenance']:
                        if key in self.prompts: tasks.append(self._dispatch(session,f'extract_{key}',self.prompts[key],images))
                elif name in ['income_statement','balance_sheet']:
                    if 'financial_statement' in self.prompts: tasks.append(self._dispatch(session,f'extract_{name}',self.prompts['financial_statement'],images))
                elif name=='multi_year_overview':
                    if 'multi_year_overview' in self.prompts: tasks.append(self._dispatch(session,'extract_multi_year',self.prompts['multi_year_overview'],images))
                elif name=='notes':
                    for p in range(start,end+1):
                        pk=self._map_note_to_prompt_key(p)
                        if pk and pk in self.prompts:
                            img=self._page_images_b64(p,p)
                            tasks.append(self._dispatch(session,f'note_p{p}_{pk}',self.prompts[pk],img))
            batches=await asyncio.gather(*tasks)
            for b in batches: results=self._deep_merge(results,b)
        self.doc.close(); return results
    
    def extract_enhanced_sectioning(self, qwen_agent) -> Dict[str, Any]:
        """
        Extract document sections using HF sectioning improvements.
        Uses bounded prompts, hierarchical post-filtering, and HMAC receipts.
        """
        if not self.enable_hf_sectioning:
            logger.info("🔍 HF sectioning disabled, using heuristic mode")
            return self._fallback_to_heuristic_sectioning()
        
        logger.info("🚀 Starting enhanced HF sectioning extraction...")
        
        # Get headers using enhanced QwenAgent
        sectioning_result = qwen_agent.get_sectioning_headers(self.pdf_path)
        
        if not sectioning_result.get("headers"):
            logger.warning("⚠️  No headers found, falling back to heuristic")
            return self._fallback_to_heuristic_sectioning()
        
        # Apply post-filtering with hierarchical logic
        processed_result = self.post_filter.process_extraction_result({
            "success": True,
            "data": sectioning_result["headers"]
        })
        
        if not processed_result.get("success"):
            logger.error("❌ Post-filtering failed, falling back to heuristic")
            return self._fallback_to_heuristic_sectioning()
        
        # Convert processed headers to section map format
        section_map = self._headers_to_section_map(processed_result["data"])
        
        logger.info(f"✅ Enhanced sectioning complete: {len(section_map)} sections identified")
        
        return {
            "section_map": section_map,
            "raw_headers": sectioning_result["headers"],
            "processed_headers": processed_result["data"],
            "stats": processed_result.get("post_filter_stats", {}),
            "method": "hf_enhanced"
        }
    
    def _headers_to_section_map(self, headers: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Convert hierarchical headers to section map format compatible with existing pipeline"""
        section_map = {}
        
        # Group headers by section type and page ranges
        current_section = None
        section_start = 1
        
        for i, header in enumerate(headers):
            page = header.get("page", 1)
            text = header.get("text", "").lower()
            level = header.get("level", 2)
            
            # Determine canonical section name based on header text
            canonical_name = self._map_header_to_canonical_section(text)
            
            # If this is a major section header (level 1), start a new section
            if level == 1 and canonical_name != "other":
                # Close previous section
                if current_section and current_section in section_map:
                    section_map[current_section]["end_page"] = page - 1
                
                # Start new section
                section_key = f"{canonical_name}_{page}"
                section_map[section_key] = {
                    "start_page": page,
                    "end_page": page,  # Will be updated later
                    "canonical_name": canonical_name
                }
                current_section = section_key
                section_start = page
            
            # Update end page for current section
            elif current_section and current_section in section_map:
                section_map[current_section]["end_page"] = page
        
        # Ensure last section ends at document end
        if current_section and current_section in section_map:
            section_map[current_section]["end_page"] = len(self.doc)
        
        # Handle case where no major sections were found - create a general section
        if not section_map:
            section_map["document_1"] = {
                "start_page": 1,
                "end_page": len(self.doc),
                "canonical_name": "management_report"
            }
        
        return section_map
    
    def _map_header_to_canonical_section(self, text: str) -> str:
        """Map Swedish header text to canonical section names"""
        text = text.lower().strip()
        
        if any(word in text for word in ['förvaltningsberättelse', 'verksamhetsberättelse']):
            return 'management_report'
        elif any(word in text for word in ['resultaträkning', 'resultat']):
            return 'income_statement'  
        elif any(word in text for word in ['balansräkning', 'balans']):
            return 'balance_sheet'
        elif 'kassaflöde' in text:
            return 'cash_flow_statement'
        elif 'flerårs' in text:
            return 'multi_year_overview'
        elif 'noter' in text:
            return 'notes'
        elif 'revision' in text:
            return 'auditors_report'
        elif any(word in text for word in ['innehåll', 'förteckning']):
            return 'table_of_contents'
        else:
            return 'other'
    
    def _fallback_to_heuristic_sectioning(self) -> Dict[str, Any]:
        """Fallback to simple heuristic sectioning if HF method fails"""
        from .agent_sectionizer import SectionizerAgent
        
        sectionizer = SectionizerAgent(self.pdf_path, mode='heuristic')
        section_map = sectionizer.analyze_document()
        
        return {
            "section_map": section_map,
            "method": "heuristic_fallback"
        }

if __name__=='__main__':
    import argparse, asyncio as _asyncio
    p=argparse.ArgumentParser()
    p.add_argument('--pdf',required=True); p.add_argument('--section_map',required=True)
    p.add_argument('--out',default='final_extraction.json'); p.add_argument('--prompts',required=True)
    a=p.parse_args()
    prompts=load_prompts(a.prompts); agent=OrchestratorAgent(a.pdf,prompts=prompts)
    section_map=json.load(open(a.section_map,'r',encoding='utf-8'))
    final=_asyncio.run(agent.run_workflow(section_map))
    open(a.out,'w',encoding='utf-8').write(json.dumps(final,ensure_ascii=False,indent=2))
    print(f'✅ Orchestration complete. Final JSON saved to {a.out}')
