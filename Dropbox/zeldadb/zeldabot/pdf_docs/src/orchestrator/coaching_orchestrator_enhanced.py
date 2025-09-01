#!/usr/bin/env python3
"""
Enhanced Coaching Orchestrator with Prompt Sync
- Uses JSON cache for fast prompt retrieval
- Updates both DB and JSON when coaching improves prompts
- Maintains sync between file and database systems
"""
import os
import json
import psycopg2
import asyncio
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.gemini_evaluator import GeminiEvaluator
from utils.prompt_sync import PromptSyncSystem

# Add JSON handler for HF-Direct output
sys.path.insert(0, '/tmp/zeldabot/pdf_docs')
try:
    from tests.test_card_4_json_handler import JsonOutputHandler
    json_handler = JsonOutputHandler()
except ImportError:
    json_handler = None
    print("⚠️ JsonOutputHandler not found, JSON cleaning disabled")

class EnhancedCoachingOrchestrator:
    def __init__(self, base_orchestrator, qwen_agent, gemini_agent, db_url):
        """
        Initialize enhanced coaching orchestrator with prompt sync
        
        Args:
            base_orchestrator: Original orchestrator instance
            qwen_agent: QwenAgent instance (with HF-Direct support)
            gemini_agent: GeminiAgent instance
            db_url: PostgreSQL database connection string
        """
        self.orchestrator = base_orchestrator
        self.qwen = qwen_agent
        self.gemini = gemini_agent
        self.db_url = db_url
        self.evaluator = GeminiEvaluator(gemini_agent)
        
        # Initialize prompt sync system
        self.prompt_sync = PromptSyncSystem(db_url)
        
        # Sync prompts on initialization
        print("🔄 Syncing prompts from database...")
        self.prompt_sync.sync_from_db_to_json()
        
        # Configuration
        self.max_rounds = int(os.environ.get("MAX_COACHING_ROUNDS", "5"))
        self.target_accuracy = float(os.environ.get("TARGET_ACCURACY", "0.85"))
        
    def get_prompt_for_section(self, section: str) -> str:
        """
        Get the best prompt for a section from JSON cache
        Falls back to basic prompt if not found
        """
        # Try JSON cache first (fast)
        prompt = self.prompt_sync.get_prompt_for_section(section)
        
        if prompt:
            print(f"   📖 Using specialized prompt for {section} from cache")
            return prompt
        
        # Fallback to basic prompt
        print(f"   ⚠️ No specialized prompt for {section}, using default")
        return f"Extract {section} information from this Swedish BRF annual report. Return JSON with all relevant fields."
    
    def get_agent_id_for_section(self, section: str) -> str:
        """Map section to agent_id for updates"""
        # Load cache to get section mapping
        cache_data = self.prompt_sync.load_prompts_from_json()
        section_mapping = cache_data.get("section_mapping", {})
        
        # Get agent IDs for this section
        agent_ids = section_mapping.get(section, [])
        if agent_ids:
            return agent_ids[0]
        
        # Try direct mapping
        possible_id = f"{section}_agent"
        if possible_id in cache_data.get("agents", {}):
            return possible_id
        
        # Default
        return f"{section}_agent"
        
    def clean_json_output(self, raw_output: Any) -> Dict:
        """Clean HF-Direct markdown-fenced JSON output"""
        if json_handler and isinstance(raw_output, str):
            return json_handler.clean_qwen_output(raw_output)
        elif isinstance(raw_output, dict):
            return raw_output
        else:
            # Try to extract JSON from string
            try:
                if isinstance(raw_output, str):
                    # Remove markdown fences
                    if raw_output.startswith("```json"):
                        raw_output = raw_output[7:]
                    if raw_output.endswith("```"):
                        raw_output = raw_output[:-3]
                    return json.loads(raw_output.strip())
            except:
                pass
            return {}
    
    def store_coaching_round(self, run_id: str, doc_id: str, section: str, 
                           round: int, prompt_in: str, prompt_out: Optional[str],
                           extraction: Dict, evaluation: Dict, agent_id: str):
        """Store coaching iteration results in database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Store in prompt execution history
            cursor.execute("""
                INSERT INTO prompt_execution_history
                (doc_id, chunk_range, engineering_round, prompt_in, prompt_out, 
                 qwen_result, gemini_improvements, execution_time_ms, success)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                doc_id, section, round, prompt_in, prompt_out,
                json.dumps(extraction, ensure_ascii=False), 
                json.dumps(evaluation, ensure_ascii=False),
                0,  # execution_time_ms placeholder
                evaluation.get("accuracy_score", 0.0) >= self.target_accuracy
            ))
            
            conn.commit()
            conn.close()
            print(f"   💾 Stored coaching round {round} for {section}")
            
        except Exception as e:
            print(f"   ❌ Failed to store coaching round: {e}")
    
    async def extract_with_coaching(self, 
                                   run_id: str, 
                                   doc_id: str, 
                                   section: str, 
                                   pages: List[int], 
                                   pdf_path: str,
                                   max_rounds: Optional[int] = None) -> Dict[str, Any]:
        """
        Extract section with iterative coaching until target accuracy achieved
        Now uses JSON cache for prompts and syncs improvements back
        """
        
        if max_rounds is None:
            max_rounds = self.max_rounds
            
        print(f"\n🎯 Starting coached extraction for {section}")
        print(f"   Target: {self.target_accuracy:.0%} accuracy in max {max_rounds} rounds")
        
        # Get agent ID for this section
        agent_id = self.get_agent_id_for_section(section)
        
        # Get initial prompt from JSON cache
        base_prompt = self.get_prompt_for_section(section)
        
        # Get expected fields for this section
        expected_fields = self.evaluator.get_expected_fields(section)
        
        best_result = {}
        best_accuracy = 0.0
        best_prompt = base_prompt
        converged = False
        
        for round_num in range(max_rounds):
            start_time = time.time()
            
            # Use appropriate prompt for this round
            if round_num == 0:
                current_prompt = base_prompt
                print(f"\n   Round {round_num + 1}: Using prompt from JSON cache")
            else:
                current_prompt = best_prompt
                print(f"\n   Round {round_num + 1}: Using coached prompt")
            
            # STEP 1: Qwen extraction
            print(f"   🤖 Qwen extracting {section}...")
            extraction_result = self.qwen.extract_section(
                section, 
                current_prompt, 
                pages, 
                pdf_path
            )
            
            # Clean the output (handle markdown fences from HF-Direct)
            if extraction_result.get("success"):
                raw_data = extraction_result.get("data", {})
                extraction_data = self.clean_json_output(raw_data)
            else:
                extraction_data = {}
                print(f"   ⚠️  Extraction failed: {extraction_result.get('error', 'Unknown error')}")
            
            # STEP 2: Gemini evaluation
            print(f"   🔍 Gemini evaluating extraction...")
            evaluation = self.evaluator.evaluate_extraction(
                extraction_data, 
                expected_fields, 
                section
            )
            
            accuracy = evaluation.get("accuracy_score", 0.0)
            elapsed = time.time() - start_time
            
            print(f"   📊 Accuracy: {accuracy:.1%} (in {elapsed:.1f}s)")
            
            if evaluation.get("missing_fields"):
                print(f"   ❌ Missing: {', '.join(evaluation['missing_fields'])}")
            
            # Track best result
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_result = extraction_data
                print(f"   ✨ New best result!")
            
            # STEP 3: Check if we should continue
            if accuracy >= self.target_accuracy:
                print(f"   ✅ Target accuracy achieved: {accuracy:.1%}")
                converged = True
                improved_prompt = None
                
                # If we improved the prompt, update DB and JSON
                if best_prompt != base_prompt:
                    print(f"   🔄 Syncing improved prompt to DB and JSON...")
                    coaching_metadata = {
                        "rounds": round_num + 1,
                        "final_accuracy": accuracy,
                        "improvement": accuracy - evaluation.get("initial_accuracy", 0)
                    }
                    self.prompt_sync.update_prompt_after_coaching(
                        agent_id, best_prompt, coaching_metadata
                    )
                
            elif round_num < max_rounds - 1:
                # STEP 4: Generate improved prompt
                print(f"   🧠 Gemini generating coaching improvements...")
                improved_prompt = self.evaluator.generate_coached_prompt(
                    current_prompt, 
                    extraction_data, 
                    evaluation, 
                    section
                )
                
                if improved_prompt and improved_prompt != current_prompt:
                    best_prompt = improved_prompt
                    print(f"   💡 Received coaching improvements")
                else:
                    improved_prompt = None
                    print(f"   ⚠️  No improvements suggested")
            else:
                improved_prompt = None
                print(f"   🔚 Max rounds reached")
            
            # Store this coaching round
            self.store_coaching_round(
                run_id, doc_id, section, round_num,
                current_prompt, improved_prompt,
                extraction_data, evaluation, agent_id
            )
            
            if converged:
                break
        
        # Final sync if we made improvements
        if best_prompt != base_prompt and best_accuracy > 0.5:
            print(f"\n   🎯 Final sync of improved prompt to DB and JSON")
            coaching_metadata = {
                "rounds": round_num + 1,
                "final_accuracy": best_accuracy,
                "section": section,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.prompt_sync.update_prompt_after_coaching(
                agent_id, best_prompt, coaching_metadata
            )
        
        # Summary
        print(f"\n📈 Coaching complete for {section}:")
        print(f"   Rounds used: {round_num + 1}")
        print(f"   Final accuracy: {best_accuracy:.1%}")
        print(f"   Converged: {'Yes' if converged else 'No'}")
        if best_prompt != base_prompt:
            print(f"   Prompt improved: ✅ (synced to DB and JSON)")
        
        return {
            "section": section,
            "data": best_result,
            "accuracy": best_accuracy,
            "rounds": round_num + 1,
            "converged": converged,
            "prompt_improved": best_prompt != base_prompt
        }
    
    async def run_parallel_coaching(self, run_id: str, doc_id: str, 
                                   section_map: Dict[str, Any], 
                                   pdf_path: str) -> Dict[str, Any]:
        """
        Run coaching for multiple sections in parallel
        """
        tasks = []
        
        for section, config in section_map.items():
            pages = config.get("pages", [1, 2])
            task = self.extract_with_coaching(
                run_id, doc_id, section, pages, pdf_path
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Combine results
        combined = {
            "run_id": run_id,
            "doc_id": doc_id,
            "sections": {}
        }
        
        for result in results:
            section = result.get("section")
            combined["sections"][section] = result
        
        return combined