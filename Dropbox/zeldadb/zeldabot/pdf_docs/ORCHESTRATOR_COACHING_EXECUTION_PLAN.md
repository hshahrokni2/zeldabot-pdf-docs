# 🎯 ORCHESTRATOR + COACHING SYSTEM EXECUTION PLAN
**Created**: 2025-01-02  
**Goal**: Get orchestrator working with 24 specialized agents, coaching loop, and 95% accuracy target

---

## 📊 SYSTEM REQUIREMENTS

### Core Functionality
1. **Sectionizer** identifies document sections
2. **Orchestrator** maps sections to appropriate agents (from 24 available)
3. **Agents** extract data using database prompts (not file prompts)
4. **Gemini** evaluates results and coaches if <95% accuracy
5. **Dual Storage** saves to PostgreSQL + JSON cache
6. **Performance Tracking** monitors all metrics

### Technical Constraints
- ✅ HF-Direct only (NO Ollama)
- ✅ Max 4 parallel agents on H100
- ✅ JSON output must be valid (use jsonfixer)
- ✅ History preservation across coaching rounds
- ✅ 95% accuracy threshold for acceptance

---

## 🃏 IMPLEMENTATION CARDS

### **CARD 1: UNIFIED ORCHESTRATOR** 
**Priority**: P0 - CRITICAL
**Status**: 🔴 Not Started

#### Implementation Tasks:
```python
# 1. Merge orchestrator files
# - Take HF-Direct logic from coaching_orchestrator.py
# - Take async dispatch from agent_orchestrator.py
# - Remove ALL Ollama references
# - Add database prompt loading

class UnifiedOrchestrator:
    def __init__(self, database_url: str):
        self.conn = psycopg2.connect(database_url)
        self.agents = self.load_agents_from_db()  # Load 24 agents
        self.prompts = self.load_prompts_from_db()  # Load from agent_registry
        
    def load_agents_from_db(self):
        """Load all 24 agents from agent_registry table"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT agent_id, name, specialization, 
                   typical_sections, bounded_prompt
            FROM agent_registry
        ''')
        return {row[0]: {...} for row in cursor.fetchall()}
```

#### TDD Test:
```python
def test_unified_orchestrator():
    orch = UnifiedOrchestrator(DATABASE_URL)
    assert len(orch.agents) == 24  # All agents loaded
    assert 'GovernanceAgent' in orch.agents
    assert orch.agents['GovernanceAgent']['bounded_prompt'] is not None
    assert 'ollama' not in str(orch).lower()  # No Ollama references
```

---

### **CARD 2: SECTION-TO-AGENT MAPPER**
**Priority**: P0 - CRITICAL  
**Status**: 🔴 Not Started

#### Implementation Tasks:
```python
class SectionAgentMapper:
    """Maps document sections to specialized agents"""
    
    SECTION_MAPPINGS = {
        'governance': 'GovernanceAgent',
        'forvaltningsberattelse': 'GovernanceAgent',
        'styrelse': 'GovernanceAgent',
        'balance_sheet': 'BalanceSheetAgent',
        'balansrakning': 'BalanceSheetAgent',
        'income_statement': 'StatementsAgent',
        'resultatrakning': 'StatementsAgent',
        'loans': 'LoansDebtAgent',
        'skulder': 'LoansDebtAgent',
        'noter': ['NoterLånRäntorAgent', 'NoterAvskrivningarAgent', ...],
        # ... map all sections to appropriate agents
    }
    
    def get_agents_for_section(self, section_name: str) -> List[str]:
        """Return list of agent IDs for a section"""
        # Fuzzy match section names
        # Return appropriate agent(s)
```

#### TDD Test:
```python
def test_section_agent_mapping():
    mapper = SectionAgentMapper()
    agents = mapper.get_agents_for_section('governance')
    assert 'GovernanceAgent' in agents
    
    agents = mapper.get_agents_for_section('balansräkning')
    assert 'BalanceSheetAgent' in agents
    
    # Test fuzzy matching
    agents = mapper.get_agents_for_section('styrelse_och_ledning')
    assert 'GovernanceAgent' in agents
```

---

### **CARD 3: JOB TRACKING SYSTEM**
**Priority**: P0 - CRITICAL
**Status**: 🔴 Not Started

#### Implementation Tasks:
```python
class JobTracker:
    """Track coaching jobs with unique IDs and history"""
    
    def __init__(self, database_url: str):
        self.conn = psycopg2.connect(database_url)
        
    def create_job(self, run_id: str, doc_id: str, section: str, agent_id: str) -> str:
        """Create unique job ID and initialize tracking"""
        job_id = f"{run_id}_{doc_id}_{section}_{agent_id}_{uuid.uuid4().hex[:8]}"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO coaching_jobs 
            (job_id, run_id, doc_id, section, agent_id, status, created_at)
            VALUES (%s, %s, %s, %s, %s, 'started', NOW())
        ''', (job_id, run_id, doc_id, section, agent_id))
        
        return job_id
        
    def record_coaching_round(self, job_id: str, round_num: int, 
                            prompt: str, result: Dict, accuracy: float):
        """Record each coaching round with full history"""
        # Store prompt, result, accuracy
        # Track which prompt achieved best accuracy
```

#### TDD Test:
```python
def test_job_tracking():
    tracker = JobTracker(DATABASE_URL)
    job_id = tracker.create_job('RUN123', 'doc456', 'governance', 'GovernanceAgent')
    assert job_id.startswith('RUN123_doc456_governance_')
    
    tracker.record_coaching_round(job_id, 1, 'prompt1', {}, 0.3)
    tracker.record_coaching_round(job_id, 2, 'prompt2', {}, 0.9)
    
    best = tracker.get_best_prompt(job_id)
    assert best['round_num'] == 2
    assert best['accuracy'] == 0.9
```

---

### **CARD 4: JSON OUTPUT HANDLER**
**Priority**: P0 - CRITICAL
**Status**: 🔴 Not Started

#### Implementation Tasks:
```python
import json
from json_repair import repair_json  # or jsonfixer

class JsonOutputHandler:
    """Handle JSON output from Qwen HF and Gemini"""
    
    def clean_qwen_output(self, raw_output: str) -> Dict:
        """Clean Qwen HF output to valid JSON"""
        # Remove markdown fences
        if '```json' in raw_output:
            raw_output = raw_output.split('```json')[1].split('```')[0]
        elif '```' in raw_output:
            raw_output = raw_output.split('```')[1].split('```')[0]
            
        # Fix common issues
        # - Remove trailing commas
        # - Fix unquoted keys
        # - Handle Swedish characters
        
        try:
            return json.loads(raw_output)
        except:
            # Use json_repair as fallback
            repaired = repair_json(raw_output)
            return json.loads(repaired)
    
    def clean_gemini_output(self, raw_output: str) -> Dict:
        """Clean Gemini output to valid JSON"""
        # Similar cleaning for Gemini
```

#### TDD Test:
```python
def test_json_output_handler():
    handler = JsonOutputHandler()
    
    # Test Qwen markdown fence removal
    raw = '```json\n{"chairman": "Erik Öhman"}\n```'
    clean = handler.clean_qwen_output(raw)
    assert clean['chairman'] == 'Erik Öhman'
    
    # Test malformed JSON repair
    raw = '{chairman: "test", board_members: ["a", "b",]}'
    clean = handler.clean_qwen_output(raw)
    assert clean['chairman'] == 'test'
    assert len(clean['board_members']) == 2
```

---

### **CARD 5: DUAL STORAGE SYSTEM**
**Priority**: P1 - HIGH
**Status**: 🔴 Not Started

#### Implementation Tasks:
```python
class DualStorageSystem:
    """Store to PostgreSQL and JSON cache for low latency"""
    
    def __init__(self, database_url: str, json_cache_path: str):
        self.conn = psycopg2.connect(database_url)
        self.json_cache_path = json_cache_path
        self.cache = self.load_json_cache()
        
    def save_result(self, job_id: str, agent_id: str, result: Dict):
        """Save to both PostgreSQL and JSON"""
        # 1. Save to PostgreSQL
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO extraction_results 
            (job_id, agent_id, result_json, created_at)
            VALUES (%s, %s, %s, NOW())
        ''', (job_id, agent_id, json.dumps(result)))
        
        # 2. Update JSON cache (for low-latency reads)
        self.cache[job_id] = result
        self.flush_cache()
        
    def get_latest_prompts(self) -> Dict:
        """Get latest successful prompts from cache first, then DB"""
        # Try cache first for speed
        if 'latest_prompts' in self.cache:
            return self.cache['latest_prompts']
        
        # Fallback to DB
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT agent_id, prompt 
            FROM successful_prompts 
            WHERE accuracy >= 0.95
            ORDER BY created_at DESC
        ''')
        return dict(cursor.fetchall())
```

#### TDD Test:
```python
def test_dual_storage():
    storage = DualStorageSystem(DATABASE_URL, '/tmp/cache.json')
    
    storage.save_result('job1', 'agent1', {'data': 'test'})
    
    # Verify in PostgreSQL
    cursor = storage.conn.cursor()
    cursor.execute('SELECT result_json FROM extraction_results WHERE job_id=%s', ('job1',))
    db_result = json.loads(cursor.fetchone()[0])
    assert db_result['data'] == 'test'
    
    # Verify in JSON cache
    assert storage.cache['job1']['data'] == 'test'
```

---

### **CARD 6: GEMINI EVALUATOR WITH HISTORY**
**Priority**: P1 - HIGH
**Status**: 🔴 Not Started

#### Implementation Tasks:
```python
class GeminiEvaluatorWithHistory:
    """Gemini evaluator that preserves coaching history"""
    
    def __init__(self, gemini_agent, job_tracker):
        self.gemini = gemini_agent
        self.tracker = job_tracker
        
    def evaluate_with_history(self, job_id: str, section: str, 
                             extraction: Dict, expected_fields: List[str]) -> Dict:
        """Evaluate extraction considering previous rounds"""
        
        # Get history for this job
        history = self.tracker.get_job_history(job_id)
        
        # Build context-aware prompt
        prompt = f'''
        Evaluate this extraction for section: {section}
        
        Current extraction: {json.dumps(extraction)}
        Expected fields: {expected_fields}
        
        Previous coaching rounds: {len(history)}
        Best accuracy so far: {max(h['accuracy'] for h in history) if history else 0}
        
        Previous improvements tried:
        {self._format_history(history)}
        
        Provide NEW improvements that haven't been tried.
        If accuracy >= 95%, mark as accepted.
        '''
        
        result = self.gemini.evaluate(prompt)
        
        # Record what worked
        if result['accuracy'] > 0.85:
            self.tracker.record_successful_pattern(job_id, result)
            
        return result
```

#### TDD Test:
```python
def test_gemini_evaluator_with_history():
    mock_gemini = Mock()
    mock_tracker = Mock()
    mock_tracker.get_job_history.return_value = [
        {'round': 1, 'accuracy': 0.3, 'improvements': 'Add more fields'},
        {'round': 2, 'accuracy': 0.6, 'improvements': 'Focus on Swedish terms'}
    ]
    
    evaluator = GeminiEvaluatorWithHistory(mock_gemini, mock_tracker)
    result = evaluator.evaluate_with_history('job1', 'governance', {}, ['chairman'])
    
    # Verify history was considered
    assert mock_tracker.get_job_history.called_with('job1')
```

---

### **CARD 7: PARALLEL AGENT EXECUTOR**
**Priority**: P1 - HIGH
**Status**: 🔴 Not Started

#### Implementation Tasks:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelAgentExecutor:
    """Execute up to 4 agents in parallel on H100"""
    
    MAX_PARALLEL = 4
    
    def __init__(self, qwen_agent):
        self.qwen = qwen_agent
        self.executor = ThreadPoolExecutor(max_workers=self.MAX_PARALLEL)
        
    async def execute_agents(self, jobs: List[Dict]) -> List[Dict]:
        """Execute multiple agent jobs in parallel"""
        
        # Batch into groups of 4
        results = []
        for i in range(0, len(jobs), self.MAX_PARALLEL):
            batch = jobs[i:i+self.MAX_PARALLEL]
            
            # Run batch in parallel
            batch_futures = []
            for job in batch:
                future = self.executor.submit(
                    self.qwen.extract_section,
                    job['section'],
                    job['prompt'],
                    job['pages'],
                    job['pdf_path']
                )
                batch_futures.append((job['job_id'], future))
            
            # Collect results
            for job_id, future in batch_futures:
                try:
                    result = future.result(timeout=60)
                    results.append({'job_id': job_id, 'result': result})
                except Exception as e:
                    results.append({'job_id': job_id, 'error': str(e)})
                    
        return results
```

#### TDD Test:
```python
def test_parallel_executor():
    mock_qwen = Mock()
    mock_qwen.extract_section.return_value = {'data': 'extracted'}
    
    executor = ParallelAgentExecutor(mock_qwen)
    
    # Create 10 jobs
    jobs = [{'job_id': f'job{i}', 'section': 'test', 
             'prompt': 'extract', 'pages': [1], 'pdf_path': 'test.pdf'} 
            for i in range(10)]
    
    results = asyncio.run(executor.execute_agents(jobs))
    
    # Verify all jobs completed
    assert len(results) == 10
    # Verify max 4 ran at once (check mock call timing)
```

---

### **CARD 8: PERFORMANCE METRICS COLLECTOR**
**Priority**: P2 - MEDIUM
**Status**: 🔴 Not Started

#### Implementation Tasks:
```python
class PerformanceMetricsCollector:
    """Collect and report performance metrics"""
    
    def __init__(self, database_url: str):
        self.conn = psycopg2.connect(database_url)
        
    def record_agent_performance(self, job_id: str, agent_id: str, 
                                start_time: float, end_time: float,
                                coaching_rounds: int, final_accuracy: float):
        """Record agent performance metrics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO agent_performance_metrics
            (job_id, agent_id, execution_time_ms, coaching_rounds, 
             final_accuracy, timestamp)
            VALUES (%s, %s, %s, %s, %s, NOW())
        ''', (job_id, agent_id, (end_time - start_time) * 1000, 
              coaching_rounds, final_accuracy))
        
    def generate_report(self, run_id: str) -> Dict:
        """Generate performance report for a run"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                agent_id,
                AVG(execution_time_ms) as avg_time,
                AVG(coaching_rounds) as avg_rounds,
                AVG(final_accuracy) as avg_accuracy,
                COUNT(*) as sections_processed
            FROM agent_performance_metrics
            WHERE job_id LIKE %s
            GROUP BY agent_id
        ''', (f'{run_id}%',))
        
        return {
            'agents': dict(cursor.fetchall()),
            'total_time': sum(...),
            'overall_accuracy': avg(...)
        }
```

#### TDD Test:
```python
def test_performance_metrics():
    collector = PerformanceMetricsCollector(DATABASE_URL)
    
    collector.record_agent_performance('job1', 'agent1', 0, 10, 2, 0.9)
    collector.record_agent_performance('job2', 'agent1', 0, 8, 1, 0.95)
    
    report = collector.generate_report('RUN123')
    assert report['agents']['agent1']['avg_accuracy'] >= 0.9
    assert report['agents']['agent1']['avg_rounds'] == 1.5
```

---

### **CARD 9: INTEGRATION TEST**
**Priority**: P0 - CRITICAL
**Status**: 🔴 Not Started

#### Implementation Tasks:
```python
def test_full_orchestrator_flow():
    """Test complete flow with real PDF"""
    
    # 1. Initialize system
    orchestrator = UnifiedOrchestrator(DATABASE_URL)
    mapper = SectionAgentMapper()
    tracker = JobTracker(DATABASE_URL)
    storage = DualStorageSystem(DATABASE_URL, '/tmp/cache.json')
    
    # 2. Load test PDF
    pdf_path = 'test_data/sample_brf.pdf'
    
    # 3. Run sectionizer
    sections = sectionizer.analyze_document(pdf_path)
    assert len(sections) > 0
    
    # 4. Map sections to agents
    for section in sections:
        agents = mapper.get_agents_for_section(section['name'])
        assert len(agents) > 0
        
        # 5. Create jobs
        for agent_id in agents:
            job_id = tracker.create_job('TEST_RUN', 'test_doc', 
                                       section['name'], agent_id)
            
            # 6. Run agent with coaching
            result = orchestrator.run_with_coaching(
                job_id, agent_id, section, 
                max_rounds=5, target_accuracy=0.95
            )
            
            # 7. Verify results
            assert result['accuracy'] >= 0.85
            assert result['rounds'] <= 5
            
            # 8. Check storage
            stored = storage.get_result(job_id)
            assert stored is not None
    
    # 9. Generate performance report
    report = collector.generate_report('TEST_RUN')
    assert report['overall_accuracy'] >= 0.85
```

---

## 🚀 EXECUTION SEQUENCE

### Phase 1: Foundation (Days 1-2)
1. ✅ Card 1: Unified Orchestrator
2. ✅ Card 2: Section-to-Agent Mapper
3. ✅ Card 4: JSON Output Handler

### Phase 2: Core Loop (Days 3-4)
4. ✅ Card 3: Job Tracking System
5. ✅ Card 6: Gemini Evaluator with History
6. ✅ Card 7: Parallel Agent Executor

### Phase 3: Polish (Days 5-6)
7. ✅ Card 5: Dual Storage System
8. ✅ Card 8: Performance Metrics
9. ✅ Card 9: Integration Test

---

## 📋 H100 DEPLOYMENT CHECKLIST

### Environment Setup
```bash
# Install dependencies on H100
pip install psycopg2-binary aiohttp asyncio json-repair

# Set environment variables
export DATABASE_URL="postgresql://postgres:h100pass@localhost:5432/zelda_arsredovisning"
export USE_HF_DIRECT=true
export HF_DEVICE=cuda:0
export HF_MODEL_PATH=Qwen/Qwen2.5-VL-7B-Instruct
export GEMINI_API_KEY=[YOUR_KEY]
export GEMINI_MODEL=gemini-2.5-pro
export MAX_PARALLEL_AGENTS=4
export TARGET_ACCURACY=0.95
```

### Database Schema Updates
```sql
-- Create missing tables
CREATE TABLE IF NOT EXISTS coaching_jobs (
    job_id VARCHAR(255) PRIMARY KEY,
    run_id VARCHAR(255),
    doc_id VARCHAR(255),
    section VARCHAR(255),
    agent_id VARCHAR(255),
    status VARCHAR(50),
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255),
    agent_id VARCHAR(255),
    execution_time_ms INTEGER,
    coaching_rounds INTEGER,
    final_accuracy FLOAT,
    timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS successful_prompts (
    agent_id VARCHAR(255),
    prompt TEXT,
    accuracy FLOAT,
    created_at TIMESTAMP
);
```

---

## 🎯 SUCCESS CRITERIA

1. **Orchestrator runs** with 24 agents from database
2. **Sections mapped** correctly to specialized agents
3. **Coaching improves** accuracy from ~60% to 95%
4. **JSON output** is always valid
5. **History preserved** across coaching rounds
6. **Performance tracked** for all agents
7. **Parallel execution** works (4 agents max)
8. **Dual storage** provides fast reads and persistence

---

## 🔥 CRITICAL FIXES NEEDED

1. **Remove ALL Ollama references** - Use HF-Direct only
2. **Load prompts from database** - Not from files
3. **Install json-repair** on H100 - For JSON fixing
4. **Handle Gemini API issues** - Add retry logic with exponential backoff
5. **Preserve coaching history** - Don't lose context between rounds

---

End of execution plan. Each card has clear implementation and tests for TDD verification.