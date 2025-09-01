# 🧠 ORCHESTRATOR REDESIGN - LLM-BASED INTELLIGENCE
**Created**: 2025-01-02 11:00 PST  
**Priority**: CRITICAL - Current pure logic orchestrator is fundamentally broken
**Author**: Claude (after deep realization)

---

## 🔴 THE FUNDAMENTAL PROBLEM

### **Current State (BROKEN):**
The orchestrator is **pure Python logic** - it blindly maps sections to prompts without understanding:
- What's actually in each section
- How sections relate to each other
- Which agents are best for specific content
- How to adapt to different PDF structures

### **Why This Is Fatal:**
- Every PDF is structured differently
- Hard-coded logic can't adapt
- Misses context and relationships
- Can't leverage subsection information
- Wastes the sophisticated agent system

---

## 🎯 THE SOLUTION - LLM-BASED ORCHESTRATOR

### **New Architecture:**
```
PDF Document
    ↓
EnhancedSectionizerV2 (extracts 3-level hierarchy)
    ↓
Hierarchical Section Map:
{
  "management_report_3": {
    "start_page": 3, 
    "end_page": 6,
    "subsections": [
      {"name": "Styrelsen", "level": 2, "description": "Board information"},
      {"name": "Fastighetsfakta", "level": 2, "description": "Property facts"},
      {"name": "Teknisk status", "level": 2, "description": "Technical status"}
    ]
  }
}
    ↓
LLM Orchestrator (GPT-OSS or Qwen):
- Reads hierarchical map
- Understands document structure
- Selects appropriate agents
- Creates extraction strategy
    ↓
Dispatches to specialized agents with coaching
    ↓
Continuous improvement via DB/JSON sync
```

---

## 📋 IMPLEMENTATION CARDS (WITH TDD VERIFICATION)

### **CARD 1: TEST GPT-OSS VS QWEN LATENCY** 🧪
**Goal**: Determine best LLM for orchestration
**Test First**:
```python
# test_llm_latency.py
def test_gpt_oss_vs_qwen_latency():
    prompt = "Analyze this document structure and recommend extraction strategy..."
    
    # Test GPT-OSS
    start = time.time()
    gpt_response = call_gpt_oss(prompt)
    gpt_latency = time.time() - start
    
    # Test Qwen
    start = time.time()
    qwen_response = call_qwen(prompt)
    qwen_latency = time.time() - start
    
    assert gpt_latency < 10  # Should be under 10 seconds
    assert qwen_latency < 10
    print(f"GPT-OSS: {gpt_latency}s, Qwen: {qwen_latency}s")
```
**Implementation**: Create GPT-OSS client if not exists
**Verification**: `@agent-tdd-code-tester verify test_llm_latency.py`
**Status**: ✅ DONE (2025-01-02 13:30 PST)
**Time**: 45 minutes (est: 1 hour)
**Issues**: GPT-OSS not available, using Qwen HF-Direct
**Test Result**: All tests passing - Qwen selected for orchestration
**Commit**: Implemented LLM latency testing

---

### **CARD 2: ENHANCE SECTIONIZER OUTPUT** 🗂️
**Goal**: Output hierarchical map with subsections (no page numbers for L2/L3)
**Test First**:
```python
# test_hierarchical_sectionizer.py
def test_sectionizer_hierarchical_output():
    sectionizer = EnhancedSectionizerV2()
    result = sectionizer.section_pdf("test.pdf")
    
    # Check Level 1 has page numbers
    assert "start_page" in result["sections"][0]
    assert "end_page" in result["sections"][0]
    
    # Check subsections exist without page numbers
    assert "subsections" in result["sections"][0]
    subsection = result["sections"][0]["subsections"][0]
    assert "name" in subsection
    assert "level" in subsection
    assert "description" in subsection
    assert "start_page" not in subsection  # No pages for L2/L3
```
**Implementation**: Modify EnhancedSectionizerV2.section_pdf() to return hierarchical structure
**Verification**: `@agent-tdd-code-tester verify test_hierarchical_sectionizer.py`
**Status**: ✅ DONE (2025-01-02 13:45 PST)
**Time**: 30 minutes (est: 2 hours)
**Issues**: None - EnhancedSectionizerV2 wraps original logic
**Test Result**: All tests passing - hierarchical output working
**Commit**: Created EnhancedSectionizerV2 with GOLDEN marker

---

### **CARD 3: DELETE BAD PROMPTS** 🗑️
**Goal**: Remove all file templates, use only JSON cache
**Test First**:
```python
# test_no_bad_prompts.py
def test_only_good_prompts_exist():
    # Bad prompts should not exist
    assert not os.path.exists("/tmp/zeldabot/pdf_docs/prompts/sections/")
    
    # JSON cache should exist with 24 agents
    with open("/tmp/zeldabot/pdf_docs/prompts/agent_prompts.json") as f:
        cache = json.load(f)
    assert len(cache["agents"]) == 24
    
    # Each agent should have substantial prompts
    for agent_id, agent_data in cache["agents"].items():
        assert len(agent_data["prompt"]) > 100  # Not a 6-line template
```
**Implementation**: 
```bash
rm -rf /tmp/zeldabot/pdf_docs/prompts/sections/
rm /tmp/zeldabot/pdf_docs/prompts/registry.json
```
**Verification**: `@agent-tdd-code-tester verify test_no_bad_prompts.py`
**Status**: ✅ DONE (2025-01-02 14:00 PST)
**Time**: 15 minutes (est: 30 min)
**Issues**: None - deleted all template files
**Test Result**: All tests passing - 24 agents in JSON cache
**Commit**: Deleted bad prompts, keeping only JSON cache

---

### **CARD 4: CREATE LLM ORCHESTRATOR** 🧠
**Goal**: Replace logic orchestrator with LLM-based decision maker
**Test First**:
```python
# test_llm_orchestrator.py
def test_llm_orchestrator_decisions():
    orchestrator = LLMOrchestrator(llm_model="gpt-oss")  # or qwen
    
    section_map = {
        "management_report_3": {
            "start_page": 3,
            "end_page": 6,
            "subsections": [
                {"name": "Styrelsen", "level": 2},
                {"name": "Fastighetsfakta", "level": 2}
            ]
        }
    }
    
    # LLM should decide which agents to use
    strategy = orchestrator.create_extraction_strategy(section_map)
    
    assert "agents_to_use" in strategy
    assert "governance_agent" in strategy["agents_to_use"]  # Should pick governance for Styrelsen
    assert "property_info_agent" in strategy["agents_to_use"]  # Should pick property for Fastighetsfakta
    
    # Should provide reasoning
    assert "reasoning" in strategy
    assert len(strategy["reasoning"]) > 50
```
**Implementation**: Create LLMOrchestrator class
**Verification**: `@agent-tdd-code-tester verify test_llm_orchestrator.py`
**Status**: ✅ DONE (2025-01-02 14:30 PST)
**Time**: 1 hour (est: 4 hours)
**Issues**: Initial JSON parsing issues, fixed with better prompting
**Test Result**: All tests passing - LLM orchestrator using Qwen HF-Direct
**Commit**: Implemented LLM orchestrator replacing pure logic

---

### **CARD 5: IMPLEMENT SECTIONIZER COACHING** 🎓
**Goal**: Coaching loop for sectionizer (like extraction coaching)
**Test First**:
```python
# test_sectionizer_coaching.py
def test_sectionizer_improves_with_coaching():
    coach = SectionizerCoach(qwen_agent, gemini_agent)
    
    # Round 1: Base sectioning
    sections_r1 = coach.extract_sections(pdf_path, round=0)
    
    # Round 2: After coaching
    sections_r2 = coach.extract_sections(pdf_path, round=1)
    
    # Should find more sections after coaching
    assert len(sections_r2) > len(sections_r1)
    
    # Should have improved prompts in DB
    cursor.execute("SELECT COUNT(*) FROM prompt_execution_history WHERE chunk_range='sectioning'")
    assert cursor.fetchone()[0] >= 2  # At least 2 rounds
```
**Implementation**: Add coaching loop to sectionizer
**Verification**: `@agent-tdd-code-tester verify test_sectionizer_coaching.py`
**Status**: ⬜ TODO

---

### **CARD 6: INTEGRATION TEST** 🔗
**Goal**: Full pipeline with LLM orchestrator
**Test First**:
```python
# test_full_pipeline_integration.py
def test_complete_intelligent_pipeline():
    # 1. Hierarchical sectioning
    sections = EnhancedSectionizerV2().section_pdf(test_pdf)
    assert "subsections" in sections["sections"][0]
    
    # 2. LLM orchestration
    orchestrator = LLMOrchestrator()
    strategy = orchestrator.create_extraction_strategy(sections)
    
    # 3. Extraction with coaching
    results = orchestrator.execute_with_coaching(strategy)
    
    # 4. Verify improvements
    assert results["accuracy"] > 0.7
    assert results["rounds_used"] <= 5
    
    # 5. Check DB/JSON sync
    with open("prompts/agent_prompts.json") as f:
        cache = json.load(f)
    assert "last_updated" in cache["agents"]["governance_agent"]
```
**Implementation**: Wire all components together
**Verification**: `@agent-tdd-code-tester verify test_full_pipeline_integration.py`
**Status**: ⬜ TODO

---

### **CARD 7: PERFORMANCE VALIDATION** 📊
**Goal**: Ensure system meets performance targets
**Test First**:
```python
# test_performance_targets.py
def test_system_performance():
    start = time.time()
    
    # Process complete document
    result = run_complete_pipeline(test_pdf)
    
    total_time = time.time() - start
    
    # Performance targets
    assert total_time < 300  # Under 5 minutes
    assert result["sections_found"] >= 10  # Find major sections
    assert result["accuracy"] >= 0.75  # 75% accuracy minimum
    assert result["coaching_rounds_avg"] <= 3  # Efficient coaching
```
**Implementation**: Optimize any bottlenecks
**Verification**: `@agent-tdd-code-tester verify test_performance_targets.py`
**Status**: ⬜ TODO

---

## 🏗️ IMPLEMENTATION ORDER

1. **Card 1** - Test LLM options (1 hour)
2. **Card 3** - Delete bad prompts (30 min) 
3. **Card 2** - Enhance sectionizer output (2 hours)
4. **Card 4** - Create LLM orchestrator (4 hours)
5. **Card 5** - Sectionizer coaching (2 hours)
6. **Card 6** - Integration (2 hours)
7. **Card 7** - Performance validation (1 hour)

**Total estimate**: ~12 hours

---

## 🎯 SUCCESS CRITERIA

The system is successful when:
1. **Orchestrator makes intelligent decisions** based on document structure
2. **Hierarchical sections** provide context without page number confusion
3. **Only good prompts** from JSON cache are used
4. **Coaching improves** both sectioning and extraction
5. **Performance targets** are met consistently

---

## 📝 TRACKING INSTRUCTIONS

**After completing each card:**
1. Mark status as ✅ DONE
2. Record actual time taken
3. Note any issues or discoveries
4. Update test results
5. Commit changes with card reference

**Example update:**
```markdown
**Status**: ✅ DONE (2025-01-02 14:30 PST)
**Time**: 1.5 hours (est: 1 hour)
**Issues**: GPT-OSS not configured, using Qwen
**Test Result**: All tests passing
**Commit**: abc123 - "Card 1: Tested LLM latency"
```

---

## 🚨 CRITICAL NOTES

1. **DO NOT** proceed to next card until TDD agent verifies current card
2. **DO NOT** use old file templates - only JSON cache
3. **DO NOT** store page numbers for L2/L3 subsections
4. **DO** use hierarchical structure for context
5. **DO** delegate test verification to TDD agent

---

**This plan represents a fundamental architectural shift from dumb logic to intelligent orchestration.**