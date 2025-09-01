#!/usr/bin/env python3
"""
Coaching Orchestrator - Implements the iterative improvement loop
Coordinates between Qwen extraction and Gemini evaluation/coaching
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

# JSON handler for HF-Direct output
sys.path.insert(0, '/tmp/zeldabot/pdf_docs')
from tests.test_card_4_json_handler import JsonOutputHandler
json_handler = JsonOutputHandler()


class CoachingOrchestrator:
    def __init__(self, base_orchestrator, qwen_agent, gemini_agent, db_url):
        """
        Initialize coaching orchestrator
        
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
        
        # Configuration
        self.max_rounds = int(os.environ.get("MAX_COACHING_ROUNDS", "5"))
        self.target_accuracy = float(os.environ.get("TARGET_ACCURACY", "0.85"))
        
    def get_latest_prompt(self, doc_id: str, section: str, round: int) -> Optional[str]:
        """Fetch the latest coached prompt from database for this section"""
        if round == 0:
            return None
            
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT prompt_out 
                FROM prompt_execution_history
                WHERE doc_id = %s 
                AND chunk_range = %s 
                AND engineering_round = %s - 1
                AND prompt_out IS NOT NULL
                ORDER BY created_at DESC 
                LIMIT 1
            """, (doc_id, section, round))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                print(f"   📝 Using coached prompt from round {round-1}")
                return result[0]
                
        except Exception as e:
            print(f"   ⚠️  Could not fetch coached prompt: {e}")
            
        return None
    
    def store_coaching_round(self, run_id: str, doc_id: str, section: str, 
                           round: int, prompt_in: str, prompt_out: Optional[str],
                           extraction: Dict, evaluation: Dict):
        """Store coaching iteration results in database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Use existing schema format
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
                evaluation.get("accuracy_score", 0.0) >= 0.85  # success threshold
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
                                   base_prompt: str,
                                   pages: List[int], 
                                   pdf_path: str,
                                   max_rounds: Optional[int] = None) -> Dict[str, Any]:
        """
        Extract section with iterative coaching until target accuracy achieved
        
        This is the MAIN COACHING LOOP that implements:
        1. Qwen extraction
        2. Gemini evaluation  
        3. Prompt improvement if needed
        4. Qwen restart with improved prompt
        5. Repeat until accuracy target or max rounds
        """
        
        if max_rounds is None:
            max_rounds = self.max_rounds
            
        print(f"\n🎯 Starting coached extraction for {section}")
        print(f"   Target: {self.target_accuracy:.0%} accuracy in max {max_rounds} rounds")
        
        # Get expected fields for this section
        expected_fields = self.evaluator.get_expected_fields(section)
        
        best_result = {}
        best_accuracy = 0.0
        converged = False
        
        for round_num in range(max_rounds):
            start_time = time.time()
            
            # Get prompt for this round
            if round_num == 0:
                current_prompt = base_prompt
                print(f"\n   Round {round_num + 1}: Using base prompt")
            else:
                # Try to get coached prompt from previous round
                coached_prompt = self.get_latest_prompt(doc_id, section, round_num)
                if coached_prompt:
                    current_prompt = coached_prompt
                    print(f"\n   Round {round_num + 1}: Using coached prompt")
                else:
                    current_prompt = base_prompt
                    print(f"\n   Round {round_num + 1}: No coached prompt found, using base")
            
            # STEP 1: Qwen extraction
            print(f"   🤖 Qwen extracting {section}...")
            extraction_result = self.qwen.extract_section(
                section, 
                current_prompt, 
                pages, 
                pdf_path
            )
            
            # Parse extraction result
            if extraction_result.get("success"):
                extraction_data = extraction_result.get("data", {})
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
                    print(f"   📝 Improved prompt generated (added {len(improved_prompt) - len(current_prompt)} chars)")
                else:
                    print(f"   ⚠️  No improvement generated")
                    improved_prompt = None
            else:
                print(f"   🏁 Max rounds reached")
                improved_prompt = None
            
            # STEP 5: Store this round's data
            self.store_coaching_round(
                run_id, doc_id, section, round_num,
                current_prompt, improved_prompt, 
                extraction_data, evaluation
            )
            
            # Stop if converged
            if converged:
                break
        
        # Store final metrics
        self.store_final_metrics(run_id, doc_id, section, round_num + 1, best_accuracy, converged)
        
        print(f"\n📈 Coaching complete for {section}:")
        print(f"   Rounds used: {round_num + 1}")
        print(f"   Final accuracy: {best_accuracy:.1%}")
        print(f"   Converged: {'Yes' if converged else 'No'}")
        
        return {
            "success": True,
            "data": best_result,
            "accuracy": best_accuracy,
            "rounds": round_num + 1,
            "converged": converged
        }
    
    def store_final_metrics(self, run_id: str, doc_id: str, section: str,
                           total_rounds: int, final_accuracy: float, converged: bool):
        """Store final coaching metrics for analysis"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Use existing coaching_metrics schema - adapting to actual columns
            cursor.execute("""
                INSERT INTO coaching_metrics
                (run_id, doc_id, section, coaching_round, current_accuracy, 
                 previous_accuracy, improvement_delta, confidence_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id, doc_id, section) 
                DO UPDATE SET
                    coaching_round = EXCLUDED.coaching_round,
                    current_accuracy = EXCLUDED.current_accuracy,
                    improvement_delta = EXCLUDED.improvement_delta
            """, (
                run_id, doc_id, section, total_rounds - 1,  # coaching_round is 0-indexed
                final_accuracy, 0.0,  # previous_accuracy (start at 0)
                final_accuracy,  # improvement_delta 
                0.85 if converged else 0.5  # confidence_score based on convergence
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"   ⚠️  Failed to store metrics: {e}")
    
    async def run_full_document_with_coaching(self, 
                                             run_id: str,
                                             doc_id: str, 
                                             pdf_path: str,
                                             section_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process entire document with coaching for each section
        """
        print(f"\n🚀 Processing document {doc_id} with coaching")
        
        all_results = {}
        
        # Load base prompts
        prompts = self.orchestrator.prompts
        
        for section_key, section_info in section_map.items():
            section_name = section_info.get("canonical_name", section_key)
            start_page = section_info.get("start_page", 1)
            end_page = section_info.get("end_page", start_page)
            pages = list(range(start_page, end_page + 1))
            
            # Get base prompt for this section
            base_prompt = prompts.get(section_name, f"Extract {section_name} information")
            
            # Run coached extraction
            result = await self.extract_with_coaching(
                run_id, doc_id, section_name, 
                base_prompt, pages, pdf_path
            )
            
            if result.get("success"):
                all_results[section_name] = result.get("data", {})
        
        return all_results
    
    def get_coaching_analytics(self, doc_id: str) -> Dict[str, Any]:
        """Get coaching performance analytics for a document"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Get overall metrics
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT section) as sections_processed,
                    AVG(total_rounds) as avg_rounds,
                    AVG(final_accuracy) as avg_accuracy,
                    SUM(CASE WHEN converged THEN 1 ELSE 0 END)::float / COUNT(*) as convergence_rate
                FROM coaching_metrics
                WHERE doc_id = %s
            """, (doc_id,))
            
            metrics = cursor.fetchone()
            
            # Get per-section details
            cursor.execute("""
                SELECT section, total_rounds, final_accuracy, converged
                FROM coaching_metrics
                WHERE doc_id = %s
                ORDER BY section
            """, (doc_id,))
            
            sections = []
            for row in cursor.fetchall():
                sections.append({
                    "section": row[0],
                    "rounds": row[1],
                    "accuracy": row[2],
                    "converged": row[3]
                })
            
            conn.close()
            
            return {
                "sections_processed": metrics[0] if metrics else 0,
                "average_rounds": metrics[1] if metrics else 0,
                "average_accuracy": metrics[2] if metrics else 0,
                "convergence_rate": metrics[3] if metrics else 0,
                "section_details": sections
            }
            
        except Exception as e:
            print(f"❌ Failed to get analytics: {e}")
            return {}

