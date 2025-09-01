#!/usr/bin/env python3
"""
Gemini evaluation and coaching component
Evaluates Qwen extractions and generates improved prompts
"""
import json
import os
from typing import Dict, Any, Optional, List

class GeminiEvaluator:
    def __init__(self, gemini_agent):
        """Initialize with a Gemini agent instance"""
        self.gemini = gemini_agent
        
    def evaluate_extraction(self, 
                           extraction: Dict[str, Any], 
                           expected_fields: List[str],
                           section: str,
                           source_text: str = "") -> Dict[str, Any]:
        """
        Evaluate extraction quality and completeness
        Returns accuracy score and specific improvements needed
        """
        
        # Calculate basic coverage
        populated = sum(1 for field in expected_fields 
                       if extraction.get(field) not in [None, "", {}, []])
        coverage = populated / len(expected_fields) if expected_fields else 0
        
        # Build evaluation prompt for Gemini
        eval_prompt = f"""You are evaluating a {section} extraction from a Swedish BRF document.

Expected fields that should be extracted:
{json.dumps(expected_fields, indent=2)}

Actual extraction result:
{json.dumps(extraction, indent=2, ensure_ascii=False)}

Evaluate the extraction and return a JSON object with:
{{
    "accuracy_score": 0.0 to 1.0 based on completeness and correctness,
    "missing_fields": ["list", "of", "missing", "field", "names"],
    "incorrect_fields": ["fields", "that", "seem", "wrong"],
    "improvements": "Specific text describing what to look for in Swedish",
    "accept": true if accuracy >= 0.85, otherwise false
}}

Focus on Swedish BRF terminology:
- ordförande = chairman
- styrelse = board
- revisor = auditor
- tillgångar = assets
- skulder = debt/liabilities
- kassa = cash
"""
        
        # Get Gemini's evaluation
        try:
            eval_result = self.gemini.extract_text_section(section, eval_prompt)
            
            # Parse result if it's a string
            if isinstance(eval_result, str):
                try:
                    eval_result = json.loads(eval_result)
                except:
                    # Fallback to basic evaluation
                    eval_result = {
                        "accuracy_score": coverage,
                        "missing_fields": [f for f in expected_fields if not extraction.get(f)],
                        "accept": coverage >= 0.85
                    }
                    
        except Exception as e:
            print(f"⚠️  Gemini evaluation failed: {e}, using coverage-based evaluation")
            eval_result = {
                "accuracy_score": coverage,
                "missing_fields": [f for f in expected_fields if not extraction.get(f)],
                "accept": coverage >= 0.85
            }
        
        # Ensure all required fields are present
        return {
            "coverage": coverage,
            "accuracy_score": eval_result.get("accuracy_score", coverage),
            "missing_fields": eval_result.get("missing_fields", []),
            "incorrect_fields": eval_result.get("incorrect_fields", []),
            "improvements": eval_result.get("improvements", ""),
            "accept": eval_result.get("accept", False)
        }
    
    def generate_coached_prompt(self,
                               original_prompt: str,
                               extraction: Dict[str, Any],
                               evaluation: Dict[str, Any],
                               section: str) -> str:
        """
        Generate an improved prompt based on evaluation feedback
        Uses Gemini to create targeted improvements
        """
        
        # Build coaching request for Gemini
        coaching_prompt = f"""You are a prompt engineering expert for Swedish BRF document extraction.

Section: {section}
Missing fields: {evaluation.get('missing_fields', [])}
Incorrect fields: {evaluation.get('incorrect_fields', [])}
Specific issues: {evaluation.get('improvements', '')}

Original prompt:
{original_prompt}

Failed extraction (what Qwen returned):
{json.dumps(extraction, indent=2, ensure_ascii=False)}

Create an IMPROVED prompt that:
1. Keeps all working parts of the original prompt
2. Adds SPECIFIC Swedish keywords for missing fields
3. Provides exact patterns to look for
4. Emphasizes the location where data typically appears

For example, if 'chairman' is missing, add:
"Look specifically for 'Ordförande:' or 'Styrelseordförande:' followed by a person's name."

Return ONLY the complete improved prompt text, no explanations."""
        
        try:
            # Get Gemini's improved prompt
            response = self.gemini.extract_text_section("coaching", coaching_prompt)
            
            # Extract prompt from response
            if isinstance(response, dict):
                improved = response.get("prompt", response.get("improved_prompt", ""))
            else:
                improved = str(response)
            
            # Validate improvement
            if improved and len(improved) > len(original_prompt) * 0.5:
                return improved
            else:
                # Fallback: Add specific improvements manually
                improvements = "\n\nCOACHING IMPROVEMENTS:\n"
                
                if evaluation.get('missing_fields'):
                    improvements += f"Focus especially on finding: {', '.join(evaluation['missing_fields'])}\n"
                
                if 'chairman' in evaluation.get('missing_fields', []):
                    improvements += "Look for 'Ordförande:', 'Styrelseordförande:' followed by names.\n"
                    
                if 'auditor' in evaluation.get('missing_fields', []):
                    improvements += "Look for 'Revisor:', 'Auktoriserad revisor:', 'Revisionsberättelse' section.\n"
                    
                if 'total_assets' in evaluation.get('missing_fields', []):
                    improvements += "Look for 'SUMMA TILLGÅNGAR', 'Tillgångar totalt' with amounts in SEK.\n"
                
                return original_prompt + improvements
                
        except Exception as e:
            print(f"⚠️  Coaching generation failed: {e}, using fallback")
            # Simple fallback
            return original_prompt + f"\n\nFocus on extracting: {', '.join(evaluation.get('missing_fields', []))}"
    
    def get_expected_fields(self, section: str) -> List[str]:
        """Define expected fields for each section type"""
        
        fields_map = {
            "governance": [
                "chairman",
                "board_members", 
                "auditor",
                "auditor_company",
                "nomination_committee"
            ],
            "balance_sheet": [
                "total_assets",
                "current_assets",
                "fixed_assets",
                "loans",
                "long_term_debt",
                "short_term_debt",
                "equity",
                "cash"
            ],
            "income_statement": [
                "revenue",
                "total_revenue",
                "operating_costs",
                "financial_costs",
                "depreciation",
                "result",
                "net_result"
            ],
            "cash_flow": [
                "cash_opening",
                "cash_from_operations",
                "cash_from_investing",
                "cash_from_financing",
                "cash_change",
                "cash_closing"
            ],
            "brf_info": [
                "organization_number",
                "name",
                "address",
                "founded_year",
                "number_of_apartments"
            ]
        }
        
        return fields_map.get(section, [])