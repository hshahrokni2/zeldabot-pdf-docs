#!/usr/bin/env python3
"""
Unified Orchestrator - Merges best of both orchestrators
- Uses database prompts (24 agents from agent_registry)
- HF-Direct only (NO Ollama)
- Integrates coaching loop
- Tracks job history
"""
import os
import sys
import json
import asyncio
import aiohttp
import psycopg2
import uuid
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
DATABASE_URL = os.getenv('DATABASE_URL')
USE_HF_DIRECT = os.getenv('USE_HF_DIRECT', 'true').lower() == 'true'
HF_MODEL_PATH = os.getenv('HF_MODEL_PATH', 'Qwen/Qwen2.5-VL-7B-Instruct')
HF_DEVICE = os.getenv('HF_DEVICE', 'cuda:0')
MAX_PARALLEL_AGENTS = int(os.getenv('MAX_PARALLEL_AGENTS', '4'))
TARGET_ACCURACY = float(os.getenv('TARGET_ACCURACY', '0.95'))
MAX_COACHING_ROUNDS = int(os.getenv('MAX_COACHING_ROUNDS', '5'))

# Import agents - these should be available in the environment
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agents.qwen_agent import QwenAgent
from agents.gemini_agent import GeminiAgent


class UnifiedOrchestrator:
    """
    Unified orchestrator that:
    1. Loads 24 agents from PostgreSQL agent_registry
    2. Maps sections to appropriate agents
    3. Runs agents with coaching loop
    4. Tracks all job history
    5. Stores results in dual storage (DB + JSON)
    """
    
    def __init__(self, database_url: str, json_cache_path: str = None):
        """Initialize with database connection"""
        self.database_url = database_url
        self.conn = psycopg2.connect(database_url)
        self.json_cache_path = json_cache_path or '/tmp/orchestrator_cache.json'
        
        # Load agents and prompts from database
        self.agents = self.load_agents_from_db()
        self.section_mappings = self.load_section_mappings()
        
        # Initialize agent instances
        self.qwen_agent = QwenAgent() if USE_HF_DIRECT else None
        self.gemini_agent = GeminiAgent()
        
        # Job tracking
        self.active_jobs = {}
        
        logger.info(f"Unified Orchestrator initialized with {len(self.agents)} agents")
        
    def load_agents_from_db(self) -> Dict[str, Dict]:
        """Load all 24 agents from agent_registry table"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT agent_id, name, specialization, 
                   typical_sections, bounded_prompt, confidence_threshold
            FROM agent_registry
            WHERE status = 'active' OR status IS NULL
            ORDER BY name
        ''')
        
        agents = {}
        for row in cursor.fetchall():
            agent_id = row[0]
            agents[agent_id] = {
                'name': row[1],
                'specialization': row[2],
                'typical_sections': row[3] or [],
                'prompt': row[4],
                'confidence_threshold': float(row[5] or 0.85)
            }
            
        logger.info(f"Loaded {len(agents)} agents from database")
        return agents
        
    def load_section_mappings(self) -> Dict[str, List[str]]:
        """Create section to agent mappings based on typical_sections"""
        mappings = {}
        
        for agent_id, agent_data in self.agents.items():
            for section in agent_data['typical_sections']:
                if section not in mappings:
                    mappings[section] = []
                mappings[section].append(agent_id)
                
        # Add common variations
        section_aliases = {
            'governance': ['styrelse', 'forvaltningsberattelse'],
            'balance_sheet': ['balansrakning', 'balansräkning'],
            'income_statement': ['resultatrakning', 'resultaträkning'],
            'notes': ['noter', 'tilläggsupplysningar'],
            'loans': ['skulder', 'lån', 'krediter']
        }
        
        for primary, aliases in section_aliases.items():
            if primary in mappings:
                for alias in aliases:
                    if alias not in mappings:
                        mappings[alias] = mappings[primary]
                        
        return mappings
        
    def get_agents_for_section(self, section_name: str) -> List[str]:
        """Get appropriate agents for a section"""
        section_lower = section_name.lower()
        
        # Direct match
        if section_lower in self.section_mappings:
            return self.section_mappings[section_lower]
            
        # Fuzzy match - check if section contains known keywords
        for known_section, agent_ids in self.section_mappings.items():
            if known_section in section_lower or section_lower in known_section:
                return agent_ids
                
        # Default to general agents
        logger.warning(f"No specific agents for section '{section_name}', using defaults")
        return ['StatementsAgent', 'PropertyInfoAgent']
        
    def create_job_id(self, run_id: str, doc_id: str, section: str, agent_id: str) -> str:
        """Create unique job ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        return f"{run_id}_{doc_id}_{section}_{agent_id}_{timestamp}_{unique_id}"
        
    async def run_section_with_coaching(self, 
                                       job_id: str,
                                       section: Dict[str, Any],
                                       agent_id: str,
                                       pdf_path: str,
                                       max_rounds: int = None) -> Dict[str, Any]:
        """
        Run a single agent on a section with coaching loop
        """
        max_rounds = max_rounds or MAX_COACHING_ROUNDS
        agent_data = self.agents.get(agent_id, {})
        base_prompt = agent_data.get('prompt', '')
        
        if not base_prompt:
            logger.error(f"No prompt found for agent {agent_id}")
            return {'error': 'No prompt available'}
            
        best_result = None
        best_accuracy = 0
        
        for round_num in range(max_rounds):
            logger.info(f"Job {job_id} - Round {round_num + 1}/{max_rounds}")
            
            # Get prompt (base or coached)
            if round_num == 0:
                prompt = base_prompt
            else:
                # Get improved prompt from previous round
                prompt = self.get_coached_prompt(job_id, round_num)
                if not prompt:
                    prompt = base_prompt  # Fallback
                    
            # Run extraction
            start_time = time.time()
            
            try:
                if self.qwen_agent:
                    result = self.qwen_agent.extract_section(
                        section['name'],
                        prompt,
                        section.get('pages', []),
                        pdf_path
                    )
                else:
                    # Fallback to mock for testing
                    result = {'success': True, 'data': {}, 'mock': True}
                    
            except Exception as e:
                logger.error(f"Extraction failed: {e}")
                result = {'success': False, 'error': str(e)}
                
            execution_time = time.time() - start_time
            
            # Evaluate with Gemini
            evaluation = await self.evaluate_extraction(
                job_id, section['name'], result, agent_data, round_num
            )
            
            accuracy = evaluation.get('accuracy_score', 0)
            
            # Record this round
            self.record_coaching_round(
                job_id, round_num, prompt, result, 
                accuracy, execution_time, evaluation
            )
            
            # Track best result
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_result = result
                
            # Check if we've reached target
            if accuracy >= TARGET_ACCURACY:
                logger.info(f"Job {job_id} - Target accuracy reached: {accuracy:.2%}")
                break
                
            # Generate coached prompt for next round
            if round_num < max_rounds - 1:
                coached_prompt = evaluation.get('improved_prompt', '')
                if coached_prompt:
                    self.save_coached_prompt(job_id, round_num + 1, coached_prompt)
                    
        # Save final result
        self.save_final_result(job_id, best_result, best_accuracy, round_num + 1)
        
        return {
            'job_id': job_id,
            'agent_id': agent_id,
            'section': section['name'],
            'result': best_result,
            'accuracy': best_accuracy,
            'rounds': round_num + 1,
            'converged': best_accuracy >= TARGET_ACCURACY
        }
        
    async def evaluate_extraction(self, job_id: str, section: str, 
                                 extraction: Dict, agent_data: Dict,
                                 round_num: int) -> Dict:
        """Evaluate extraction with Gemini"""
        
        # Get job history for context
        history = self.get_job_history(job_id)
        
        evaluation_prompt = f"""
        Evaluate this extraction for section: {section}
        Agent: {agent_data.get('name', 'Unknown')}
        Specialization: {agent_data.get('specialization', 'General')}
        
        Extraction result: {json.dumps(extraction.get('data', {}), ensure_ascii=False)}
        
        This is round {round_num + 1}.
        Previous rounds: {len(history)}
        
        Evaluate:
        1. Accuracy (0-1): How accurate is the extracted data?
        2. Coverage (0-1): Are all expected fields extracted?
        3. Missing fields: List any critical missing fields
        
        If accuracy < {TARGET_ACCURACY}:
        - Provide an improved prompt that addresses the issues
        - Focus on Swedish BRF document specifics
        - Include examples of what to look for
        
        Return JSON with:
        {{
            "accuracy_score": 0.0-1.0,
            "coverage_score": 0.0-1.0,
            "missing_fields": [],
            "accept": true/false,
            "improved_prompt": "..." (if not accepted)
        }}
        """
        
        try:
            evaluation = self.gemini_agent.extract_text_section(
                section, evaluation_prompt
            )
            
            # Clean up response
            if isinstance(evaluation, str):
                evaluation = json.loads(evaluation)
                
            return evaluation
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {
                'accuracy_score': 0,
                'coverage_score': 0,
                'accept': False,
                'error': str(e)
            }
            
    def record_coaching_round(self, job_id: str, round_num: int, 
                             prompt: str, result: Dict, accuracy: float,
                             execution_time: float, evaluation: Dict):
        """Record coaching round in database"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO prompt_execution_history
                (doc_id, chunk_range, engineering_round, 
                 prompt_in, qwen_result, gemini_improvements, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ''', (
                job_id.split('_')[1],  # Extract doc_id from job_id
                job_id.split('_')[2],  # Extract section from job_id
                round_num,
                prompt,
                json.dumps(result),
                json.dumps(evaluation)
            ))
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to record coaching round: {e}")
            self.conn.rollback()
            
    def get_job_history(self, job_id: str) -> List[Dict]:
        """Get coaching history for a job"""
        cursor = self.conn.cursor()
        
        doc_id = job_id.split('_')[1]
        section = job_id.split('_')[2]
        
        cursor.execute('''
            SELECT engineering_round, prompt_in, qwen_result, gemini_improvements
            FROM prompt_execution_history
            WHERE doc_id = %s AND chunk_range = %s
            ORDER BY engineering_round
        ''', (doc_id, section))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'round': row[0],
                'prompt': row[1],
                'result': json.loads(row[2]) if row[2] else {},
                'evaluation': json.loads(row[3]) if row[3] else {}
            })
            
        return history
        
    def get_coached_prompt(self, job_id: str, round_num: int) -> Optional[str]:
        """Get coached prompt for a specific round"""
        cursor = self.conn.cursor()
        
        doc_id = job_id.split('_')[1]
        section = job_id.split('_')[2]
        
        cursor.execute('''
            SELECT prompt_out
            FROM prompt_execution_history
            WHERE doc_id = %s AND chunk_range = %s 
            AND engineering_round = %s - 1
            ORDER BY created_at DESC
            LIMIT 1
        ''', (doc_id, section, round_num))
        
        result = cursor.fetchone()
        return result[0] if result else None
        
    def save_coached_prompt(self, job_id: str, round_num: int, prompt: str):
        """Save coached prompt for next round"""
        cursor = self.conn.cursor()
        
        doc_id = job_id.split('_')[1]
        section = job_id.split('_')[2]
        
        try:
            cursor.execute('''
                UPDATE prompt_execution_history
                SET prompt_out = %s
                WHERE doc_id = %s AND chunk_range = %s 
                AND engineering_round = %s - 1
            ''', (prompt, doc_id, section, round_num))
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save coached prompt: {e}")
            self.conn.rollback()
            
    def save_final_result(self, job_id: str, result: Dict, 
                         accuracy: float, rounds: int):
        """Save final extraction result"""
        cursor = self.conn.cursor()
        
        try:
            # Save to extraction_results
            cursor.execute('''
                INSERT INTO extraction_results
                (run_id, doc_id, section, json_data, model, 
                 success, confidence_score, coaching_round, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ''', (
                job_id.split('_')[0],  # run_id
                job_id.split('_')[1],  # doc_id
                job_id.split('_')[2],  # section
                json.dumps(result.get('data', {})),
                'unified_orchestrator',
                result.get('success', False),
                accuracy,
                rounds
            ))
            
            # Also save to JSON cache for fast access
            self.update_json_cache(job_id, result, accuracy)
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save final result: {e}")
            self.conn.rollback()
            
    def update_json_cache(self, job_id: str, result: Dict, accuracy: float):
        """Update JSON cache for low-latency reads"""
        try:
            # Load existing cache
            cache = {}
            if os.path.exists(self.json_cache_path):
                with open(self.json_cache_path, 'r') as f:
                    cache = json.load(f)
                    
            # Update with new result
            cache[job_id] = {
                'result': result,
                'accuracy': accuracy,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save back
            with open(self.json_cache_path, 'w') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update JSON cache: {e}")
            
    async def run_document(self, run_id: str, doc_id: str, 
                          pdf_path: str, section_map: Dict) -> Dict:
        """
        Run full document extraction with all appropriate agents
        """
        logger.info(f"Processing document {doc_id} with {len(section_map)} sections")
        
        all_results = {}
        tasks = []
        
        for section_name, section_data in section_map.items():
            # Get appropriate agents for this section
            agent_ids = self.get_agents_for_section(section_name)
            
            for agent_id in agent_ids:
                # Create job
                job_id = self.create_job_id(run_id, doc_id, section_name, agent_id)
                
                # Create task for this agent
                task = self.run_section_with_coaching(
                    job_id, 
                    {'name': section_name, **section_data},
                    agent_id,
                    pdf_path
                )
                tasks.append(task)
                
                # Limit parallel execution
                if len(tasks) >= MAX_PARALLEL_AGENTS:
                    # Wait for batch to complete
                    batch_results = await asyncio.gather(*tasks)
                    for result in batch_results:
                        all_results[result['job_id']] = result
                    tasks = []
                    
        # Process remaining tasks
        if tasks:
            batch_results = await asyncio.gather(*tasks)
            for result in batch_results:
                all_results[result['job_id']] = result
                
        # Generate summary
        summary = self.generate_document_summary(run_id, doc_id, all_results)
        
        return {
            'run_id': run_id,
            'doc_id': doc_id,
            'sections_processed': len(section_map),
            'agents_used': len(all_results),
            'results': all_results,
            'summary': summary
        }
        
    def generate_document_summary(self, run_id: str, doc_id: str, 
                                 results: Dict) -> Dict:
        """Generate summary statistics for document processing"""
        
        total_accuracy = sum(r.get('accuracy', 0) for r in results.values())
        avg_accuracy = total_accuracy / len(results) if results else 0
        
        total_rounds = sum(r.get('rounds', 0) for r in results.values())
        converged_count = sum(1 for r in results.values() if r.get('converged', False))
        
        return {
            'average_accuracy': avg_accuracy,
            'total_coaching_rounds': total_rounds,
            'converged_sections': converged_count,
            'total_sections': len(results),
            'success_rate': converged_count / len(results) if results else 0
        }


# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Orchestrator")
    parser.add_argument('--pdf', required=True, help="PDF file path")
    parser.add_argument('--run-id', required=True, help="Run ID")
    parser.add_argument('--doc-id', required=True, help="Document ID")
    parser.add_argument('--section-map', required=True, help="Section map JSON file")
    
    args = parser.parse_args()
    
    # Load section map
    with open(args.section_map, 'r') as f:
        section_map = json.load(f)
        
    # Initialize orchestrator
    orchestrator = UnifiedOrchestrator(DATABASE_URL)
    
    # Run document processing
    results = asyncio.run(orchestrator.run_document(
        args.run_id, args.doc_id, args.pdf, section_map
    ))
    
    # Output results
    print(json.dumps(results, ensure_ascii=False, indent=2))