# 🎯 H100 HF-Direct Phase 2 Execution Plan

## 📊 Issue Analysis Summary

**Configuration Inconsistency Confirmed:**
- Documentation claims "HF Direct success" while environment scripts require Ollama
- `preflight.sh` validates `OLLAMA_URL` and `ollama --version` (lines 29-34)
- `run_prod.py` requires `OLLAMA_URL` as mandatory environment variable
- Orchestrator uses `QWEN_VL_API_URL` pointing to Ollama, not HF transformers

**Root Cause**: Hybrid architecture with incomplete migration from Ollama to HF-Direct

## 🎯 5-PDF HF-Direct Proof-of-Concept Plan

### Step A: H100 Session Setup with HF-Direct Environment

```bash
# Set pure HF-Direct environment (no Ollama dependencies)
export DATABASE_URL="postgresql://postgres:h100pass@localhost:15432/zelda_arsredovisning"
export USE_HF_DIRECT="true"
export HF_DEVICE="cuda:0"
export HF_MODEL_PATH="Qwen/Qwen2.5-VL-7B-Instruct"
export TWIN_AGENTS="1"
export GEMINI_API_KEY="AIzaSyD0y92BjcnvUgRlWsA1oPSIWV5QaJcCrNw"
export GEMINI_MODEL="gemini-2.5-pro"
```

### Step B: Prove HF-Direct Execution (Not Ollama)

**Required Verification Lines:**
1. `✅ CUDA Device: NVIDIA H100 80GB HBM3` 
2. `✅ HF Transformers: Qwen2.5-VL components loaded`
3. `✅ Transport Mode: HF_DIRECT`
4. `✅ Ollama Bypass: (ignored in HF-Direct)`

### Step C: 5-PDF Dual Extraction with Verifiable Logging

**Architecture:**
- Direct instantiation of `QwenAgent(USE_HF_DIRECT=true)` + `GeminiAgent()`
- Bypass orchestrator (which still uses Ollama endpoints)
- Process 5 documents with both agents simultaneously
- Log all calls to database with RUN_ID tracking

### Step D: DB-Level Proof with Specific RUN_ID Queries

**Required Database Evidence:**
- Table: `hf_direct_poc_results` with agent_type, model_name, transport_mode
- Query: `SELECT agent_type, COUNT(*) FROM hf_direct_poc_results WHERE run_id = 'RUN_ID' GROUP BY agent_type`
- Expected: 5 Qwen + 5 Gemini records for dual extraction proof

### Step E: Evidence Pack with Git Commit

**Deliverables:**
1. Complete results JSON with verification lines
2. Database count verification
3. Git commit with evidence artifacts
4. Performance metrics and success rates

## 🚀 Execution Commands

### Local Diagnostic First:
```bash
# Test HF-Direct readiness locally
python3 hf_direct_diagnostic.py
```

### H100 POC Execution:
```bash
# Full 5-PDF POC on H100
./run_hf_direct_poc.sh
```

### Manual H100 Verification:
```bash
# SSH to H100 and run POC directly
ssh -p 26983 -i ~/.ssh/BrfGraphRag root@45.135.56.10
cd /tmp && python3 h100_hf_direct_poc.py
```

## 📋 Expected Output Format

### RUN_ID from Step A:
```
🎯 H100 HF-DIRECT POC: HF_DIRECT_POC_1735689234
```

### Four CUDA/Transport Verification Lines from Step B:
```
✅ CUDA Device: NVIDIA H100 80GB HBM3
✅ HF Transformers: Qwen2.5-VL components loaded  
✅ Transport Mode: HF_DIRECT
✅ Ollama Bypass: http://127.0.0.1:11434 (ignored in HF-Direct)
```

### Database Result Tables:
```sql
-- Expected output showing dual extraction proof
SELECT agent_type, COUNT(*) as count, AVG(latency_ms) as avg_latency
FROM hf_direct_poc_results 
WHERE run_id = 'HF_DIRECT_POC_1735689234'
GROUP BY agent_type;

-- Expected result:
-- gemini | 5 | 3500.0
-- qwen   | 5 | 1800.0
```

### Git Branch + Commit SHA:
```
📦 Evidence pack created: artifacts/hf_direct_poc_HF_DIRECT_POC_1735689234/
✅ Git commit created: a1b2c3d4
```

## 🏗️ Architecture Recommendations

### Immediate (Phase 2):
1. **Bypass Configuration Conflicts**: Use direct agent instantiation, skip orchestrator
2. **Clean Environment Separation**: Pure HF-Direct variables, ignore Ollama requirements  
3. **Database Proof**: Create dedicated poc results table with verifiable counts

### Long-term (Phase 3):
1. **Complete Ollama Removal**: Update preflight.sh, run_prod.py environment requirements
2. **Orchestrator Migration**: Refactor OrchestratorAgent to use HF-Direct natively
3. **Configuration Cleanup**: Single source of truth for transport mode

## 🎯 Success Criteria

**Minimum Viable Proof:**
- ≥3/5 documents successfully processed by both agents
- Database records proving HF-Direct transport mode
- Verifiable CUDA execution on H100
- Git commit with complete evidence pack

**Quality Gates:**
- Qwen average latency <3000ms (HF-Direct efficiency)
- Gemini average latency <5000ms (Vertex AI performance)  
- Zero Ollama endpoint calls in logs
- JSON parsing success rate ≥80%

This plan provides **concrete, verifiable proof** of HF-Direct execution while bypassing the current configuration conflicts.