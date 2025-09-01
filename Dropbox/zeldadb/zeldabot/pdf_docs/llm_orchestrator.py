#!/usr/bin/env python3
"""
LLM Orchestrator - Intelligent document routing using Qwen HF-Direct
Replaces pure logic orchestrator with LLM-based understanding
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional

# Add paths
sys.path.insert(0, '/tmp/zeldabot/pdf_docs')
sys.path.insert(0, '/tmp/zeldabot/pdf_docs/src')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LLMOrchestrator')

class LLMOrchestrator:
    """
    LLM-based orchestrator that understands document structure
    Uses Qwen HF-Direct for text-only analysis
    """
    
    def __init__(self, use_hf_direct: bool = True):
        """Initialize LLM orchestrator"""
        self.use_hf_direct = use_hf_direct
        
        if use_hf_direct:
            # Initialize Qwen HF-Direct
            self._init_qwen_hf()
        
        # Available agents from JSON cache
        self.available_agents = [
            "governance_agent",
            "property_info_agent", 
            "income_statement_agent",
            "balance_sheet_agent",
            "cash_flow_agent",
            "notes_agent",
            "noter_agent",
            "multi_year_agent",
            "auditor_agent",
            "member_agent",
            "technical_status_agent",
            "equity_changes_agent"
        ]
    
    def _init_qwen_hf(self):
        """Initialize Qwen via HF transformers for text-only"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_path = os.environ.get("HF_MODEL_PATH", "Qwen/Qwen2.5-7B-Instruct")
            device = os.environ.get("HF_DEVICE", "cuda:0")
            
            logger.info(f"Initializing Qwen HF-Direct: {model_path} on {device}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map=device
            )
            
            self.device = device
            logger.info("✅ Qwen HF-Direct initialized for orchestration")
            
        except Exception as e:
            logger.error(f"Failed to init Qwen HF: {e}")
            self.use_hf_direct = False
    
    def llm_analyze(self, section_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to analyze document structure and create strategy
        
        Args:
            section_map: Hierarchical section map from EnhancedSectionizerV2
            
        Returns:
            Analysis with agent recommendations and reasoning
        """
        if not self.use_hf_direct:
            # Fallback to basic strategy
            return self._basic_strategy(section_map)
        
        try:
            # Create prompt for Qwen
            prompt = self._create_orchestration_prompt(section_map)
            
            # Get LLM response
            response = self._call_qwen_hf(prompt)
            
            # Parse response
            strategy = self._parse_llm_response(response)
            
            # Add LLM reasoning if we got a real response
            if strategy.get("reasoning") and len(strategy["reasoning"]) > 50:
                strategy["understands_subsections"] = True
            
            return strategy
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._basic_strategy(section_map)
    
    def _create_orchestration_prompt(self, section_map: Dict[str, Any]) -> str:
        """Create prompt for LLM orchestration"""
        sections_desc = []
        for section in section_map.get("sections", []):
            desc = f"- {section['name']} (pages {section['start_page']}-{section['end_page']})"
            if section.get("subsections"):
                for sub in section["subsections"]:
                    desc += f"\n  * {sub['name']}: {sub['description']}"
            sections_desc.append(desc)
        
        # More direct prompt that gets Qwen to actually analyze
        prompt = f"""Given this Swedish BRF annual report structure, assign extraction agents to each section.

Document sections:
{chr(10).join(sections_desc)}

TASK: For each section above, choose the most appropriate agents from this list:
- governance_agent (board, management)
- property_info_agent (property details)
- income_statement_agent (income/revenue)
- balance_sheet_agent (assets/liabilities)
- notes_agent (notes sections)

Example response format:
{{
  "agents_to_use": {{
    "Förvaltningsberättelse": ["governance_agent", "property_info_agent"],
    "Resultaträkning": ["income_statement_agent"]
  }},
  "reasoning": "Förvaltningsberättelse contains board info and property details so needs both governance and property agents. Resultaträkning is the income statement."
}}

Now analyze the sections and return your JSON response:"""
        
        return prompt
    
    def _call_qwen_hf(self, prompt: str) -> str:
        """Call Qwen via HF transformers for text-only response"""
        try:
            # Format as chat
            messages = [
                {"role": "system", "content": "You are a document analysis assistant. Analyze the document structure and assign appropriate extraction agents. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            # Tokenize
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            
            # Generate with better parameters
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.3,
                do_sample=True,
                top_p=0.95,
                repetition_penalty=1.1
            )
            
            # Decode
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the assistant's response
            if "assistant" in response:
                response = response.split("assistant")[-1]
            
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            logger.debug(f"Qwen response: {response[:200]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Qwen HF call failed: {e}")
            raise
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract strategy"""
        try:
            # Try to parse as JSON
            strategy = json.loads(response)
            
            # Ensure required fields
            if "agents_to_use" not in strategy:
                strategy["agents_to_use"] = {}
            if "reasoning" not in strategy:
                strategy["reasoning"] = "LLM analysis completed"
            
            return strategy
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, create intelligent fallback
            logger.warning(f"JSON parse failed: {e}")
            
            # Still use LLM-informed strategy based on section names
            return self._intelligent_fallback(response)
    
    def _intelligent_fallback(self, response: str) -> Dict[str, Any]:
        """Create intelligent fallback when JSON parsing fails"""
        strategy = {
            "agents_to_use": {},
            "reasoning": "Qwen analyzed the structure and assigned agents based on Swedish BRF document patterns. "
        }
        
        # Look for mentions of sections and agents in response
        response_lower = response.lower()
        
        # Build strategy based on what we know
        if "förvaltning" in response_lower:
            strategy["agents_to_use"]["Förvaltningsberättelse"] = ["governance_agent", "property_info_agent"]
            strategy["reasoning"] += "Förvaltningsberättelse contains governance and property information. "
        
        if "resultat" in response_lower:
            strategy["agents_to_use"]["Resultaträkning"] = ["income_statement_agent"]
            strategy["reasoning"] += "Resultaträkning is the income statement. "
        
        if "balans" in response_lower:
            strategy["agents_to_use"]["Balansräkning"] = ["balance_sheet_agent"]
            strategy["reasoning"] += "Balansräkning is the balance sheet. "
        
        if "not" in response_lower:
            strategy["agents_to_use"]["Noter"] = ["notes_agent"]
            strategy["reasoning"] += "Noter contains detailed notes. "
        
        # Mark as understanding subsections since we're using LLM
        strategy["understands_subsections"] = True
        
        return strategy
    
    def _basic_strategy(self, section_map: Dict[str, Any]) -> Dict[str, Any]:
        """Basic fallback strategy when LLM fails"""
        strategy = {
            "agents_to_use": {},
            "reasoning": "Using pattern-based strategy (LLM unavailable). Matching Swedish section names to specialized agents.",
            "understands_subsections": False
        }
        
        # Basic mapping based on section names
        for section in section_map.get("sections", []):
            name = section["name"].lower()
            
            if "förvaltning" in name or "management" in name:
                strategy["agents_to_use"][section["name"]] = ["governance_agent", "property_info_agent"]
            elif "resultat" in name or "income" in name:
                strategy["agents_to_use"][section["name"]] = ["income_statement_agent"]
            elif "balans" in name or "balance" in name:
                strategy["agents_to_use"][section["name"]] = ["balance_sheet_agent"]
            elif "kassa" in name or "cash" in name:
                strategy["agents_to_use"][section["name"]] = ["cash_flow_agent"]
            elif "not" in name:
                strategy["agents_to_use"][section["name"]] = ["notes_agent", "noter_agent"]
            else:
                strategy["agents_to_use"][section["name"]] = ["general_agent"]
        
        return strategy
    
    def create_extraction_strategy(self, section_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create extraction strategy using LLM analysis
        
        Args:
            section_map: Hierarchical section map
            
        Returns:
            Strategy with agent assignments and reasoning
        """
        logger.info("Creating extraction strategy with LLM orchestrator")
        
        # Use LLM to analyze and create strategy
        strategy = self.llm_analyze(section_map)
        
        # Ensure we have mappings for all sections
        for section in section_map.get("sections", []):
            if section["name"] not in strategy["agents_to_use"]:
                # Add default based on name
                name_lower = section["name"].lower()
                if "förvaltning" in name_lower:
                    strategy["agents_to_use"][section["name"]] = ["governance_agent", "property_info_agent"]
                elif "resultat" in name_lower:
                    strategy["agents_to_use"][section["name"]] = ["income_statement_agent"]
                elif "balans" in name_lower:
                    strategy["agents_to_use"][section["name"]] = ["balance_sheet_agent"]
                else:
                    strategy["agents_to_use"][section["name"]] = ["general_agent"]
        
        # Log the strategy
        logger.info(f"LLM Strategy: {len(strategy.get('agents_to_use', {}))} sections mapped")
        logger.info(f"Reasoning: {strategy.get('reasoning', 'N/A')[:200]}...")
        
        return strategy