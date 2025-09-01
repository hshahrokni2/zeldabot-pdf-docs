#!/usr/bin/env python3
"""
LLM Orchestrator Selector - Implementation to make Card 1 tests pass
This is the GREEN phase of TDD - minimal implementation to pass tests
"""
import time
import os
import sys
import json
from typing import Dict, Any, List, Optional

# Add paths for imports
sys.path.insert(0, '/tmp/zeldabot/pdf_docs')
sys.path.insert(0, '/tmp/zeldabot/pdf_docs/src')

class LLMOrchestratorSelector:
    """Selects best available LLM for orchestration tasks"""
    
    def __init__(self):
        """Initialize selector with available models"""
        self.models = {
            "gpt-oss": {"available": False, "path": "/tmp/models/gpt-oss"},
            "qwen": {"available": True, "module": "src.agents.qwen_agent"},
            "gemini": {"available": True, "api_key": os.environ.get("GEMINI_API_KEY")}
        }
        
        # Check GPT-OSS availability
        if os.path.exists(self.models["gpt-oss"]["path"]):
            self.models["gpt-oss"]["available"] = True
    
    def test_all_available_llms(self, prompt: str) -> List[Dict[str, Any]]:
        """Test all available LLMs with given prompt"""
        results = []
        
        # Test GPT-OSS (if available)
        if self.models["gpt-oss"]["available"]:
            result = self._test_gpt_oss(prompt)
            results.append(result)
        
        # Test Qwen
        if self.models["qwen"]["available"]:
            result = self._test_qwen(prompt)
            results.append(result)
        
        # Test Gemini
        if self.models["gemini"]["available"] and self.models["gemini"]["api_key"]:
            result = self._test_gemini(prompt)
            results.append(result)
        
        return results
    
    def _test_qwen(self, prompt: str) -> Dict[str, Any]:
        """Test Qwen model"""
        try:
            # For now, mark as unavailable for text-only orchestration
            # due to interface issues discovered in previous test
            return {
                "model": "qwen",
                "success": False,
                "error": "Interface not compatible with text-only orchestration",
                "latency": 999
            }
        except Exception as e:
            return {
                "model": "qwen",
                "success": False,
                "error": str(e),
                "latency": 999
            }
    
    def _test_gemini(self, prompt: str) -> Dict[str, Any]:
        """Test Gemini model"""
        try:
            import google.generativeai as genai
            
            api_key = self.models["gemini"]["api_key"] or "AIzaSyD0y92BjcnvUgRlWsA1oPSIWV5QaJcCrNw"
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel(
                "gemini-2.5-pro",
                generation_config={"response_mime_type": "application/json"}
            )
            
            start = time.time()
            response = model.generate_content(prompt)
            latency = time.time() - start
            
            return {
                "model": "gemini",
                "success": True,
                "response": response.text,
                "latency": latency
            }
        except Exception as e:
            return {
                "model": "gemini",
                "success": False,
                "error": str(e),
                "latency": 999
            }
    
    def _test_gpt_oss(self, prompt: str) -> Dict[str, Any]:
        """Test GPT-OSS model (stub for now)"""
        return {
            "model": "gpt-oss",
            "success": False,
            "error": "Not implemented",
            "latency": 999
        }
    
    def select_best_model(self, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select best model from test results"""
        # Filter working models
        working = [r for r in results if r["success"]]
        
        if not working:
            return None
        
        # Sort by latency and return best
        working.sort(key=lambda x: x["latency"])
        return working[0]
    
    def get_best_available_model(self) -> Optional[Dict[str, Any]]:
        """Get best available model with a simple test"""
        test_prompt = "Return JSON: {\"test\": \"success\"}"
        results = self.test_all_available_llms(test_prompt)
        return self.select_best_model(results)
    
    def create_extraction_strategy(self, sections: Dict[str, Any], model: str = None) -> Dict[str, Any]:
        """Create extraction strategy using specified or best model"""
        if model is None:
            best = self.get_best_available_model()
            if not best:
                raise ValueError("No LLM available for orchestration")
            model = best["model"]
        
        # For now, use Gemini since it's the only working one
        if model == "gemini":
            return self._create_strategy_with_gemini(sections)
        else:
            # Fallback to hardcoded strategy
            return self._create_default_strategy(sections)
    
    def _create_strategy_with_gemini(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Create strategy using Gemini"""
        try:
            import google.generativeai as genai
            
            api_key = self.models["gemini"]["api_key"] or "AIzaSyD0y92BjcnvUgRlWsA1oPSIWV5QaJcCrNw"
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel(
                "gemini-2.5-pro",
                generation_config={"response_mime_type": "application/json"}
            )
            
            prompt = f"""Given these document sections, assign appropriate extraction agents:
            
            Sections: {json.dumps(sections, indent=2)}
            
            Return JSON with structure:
            {{
                "agents_to_use": {{
                    "section_name": ["agent1", "agent2", ...]
                }}
            }}
            
            Available agents:
            - governance_agent (for board, management info)
            - property_info_agent (for property details)
            - income_statement_agent (for income statements)
            - balance_sheet_agent (for balance sheets)
            - cash_flow_agent (for cash flow)
            - notes_agent (for notes sections)
            """
            
            response = model.generate_content(prompt)
            strategy = json.loads(response.text)
            
            # Ensure proper structure
            if "agents_to_use" not in strategy:
                strategy = {"agents_to_use": strategy}
            
            return strategy
            
        except Exception as e:
            print(f"Gemini strategy creation failed: {e}")
            return self._create_default_strategy(sections)
    
    def _create_default_strategy(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Create default hardcoded strategy as fallback"""
        strategy = {"agents_to_use": {}}
        
        for section_name in sections:
            lower_name = section_name.lower()
            
            if "förvaltning" in lower_name or "management" in lower_name:
                strategy["agents_to_use"][section_name] = ["governance_agent", "property_info_agent"]
            elif "resultat" in lower_name or "income" in lower_name:
                strategy["agents_to_use"][section_name] = ["income_statement_agent"]
            elif "balans" in lower_name or "balance" in lower_name:
                strategy["agents_to_use"][section_name] = ["balance_sheet_agent"]
            elif "kassa" in lower_name or "cash" in lower_name:
                strategy["agents_to_use"][section_name] = ["cash_flow_agent"]
            elif "not" in lower_name:
                strategy["agents_to_use"][section_name] = ["notes_agent"]
            else:
                strategy["agents_to_use"][section_name] = ["general_agent"]
        
        return strategy
    
    def get_model_with_fallback(self) -> Optional[Dict[str, Any]]:
        """Get any available model with fallback logic"""
        # Try in order: GPT-OSS, Gemini, Qwen
        if self.models["gpt-oss"]["available"]:
            return {"model": "gpt-oss", "available": True}
        
        if self.models["gemini"]["available"] and self.models["gemini"]["api_key"]:
            return {"model": "gemini", "available": True}
        
        if self.models["qwen"]["available"]:
            return {"model": "qwen", "available": True}
        
        return None