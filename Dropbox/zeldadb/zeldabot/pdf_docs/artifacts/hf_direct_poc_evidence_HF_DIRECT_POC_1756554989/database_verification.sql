-- H100 HF-Direct POC Database Verification
-- RUN_ID: HF_DIRECT_POC_1756554989
-- Date: 2025-08-30

-- Query to verify dual extraction records
SELECT agent_type, COUNT(*) as count, 
       ROUND(AVG(latency_ms)::numeric, 1) as avg_latency,
       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
       transport_mode
FROM hf_direct_poc_results 
WHERE run_id = 'HF_DIRECT_POC_1756554989'
GROUP BY agent_type, transport_mode
ORDER BY agent_type;

-- Expected Results:
-- GEMINI: 5 records, 3/5 successful, avg 6540.6ms, transport: vertex_ai
-- QWEN: 5 records, 5/5 successful, avg 1165.0ms, transport: hf_direct

-- Verification of transport modes (proves HF-Direct execution)
SELECT DISTINCT transport_mode, COUNT(*) 
FROM hf_direct_poc_results 
WHERE run_id = 'HF_DIRECT_POC_1756554989'
GROUP BY transport_mode;

-- Expected Results:
-- hf_direct: 5 (Qwen records)
-- vertex_ai: 5 (Gemini records)

-- Individual document processing verification
SELECT doc_id, agent_type, success, latency_ms, transport_mode
FROM hf_direct_poc_results 
WHERE run_id = 'HF_DIRECT_POC_1756554989'
ORDER BY doc_id, agent_type;

-- Total record count verification (should be 10 total: 5 Qwen + 5 Gemini)
SELECT COUNT(*) as total_records 
FROM hf_direct_poc_results 
WHERE run_id = 'HF_DIRECT_POC_1756554989';