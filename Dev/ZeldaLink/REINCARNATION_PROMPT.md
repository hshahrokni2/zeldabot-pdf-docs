# ZeldaLink Reincarnation Guide

This file provides a concise overview of the current state of the ZeldaLink system for quick orientation after a `/compact` command.

## Current System State

1. **Core System**: A multi-tiered extraction system for Swedish Housing Association (BRF) annual reports
2. **Main Components**:
   - Document classifier
   - Pattern-based extraction for native PDFs
   - Mistral OCR for scanned documents
   - Format-specific processors for special formats
   - Vision models for complex visual elements
   - Human validation system

3. **Recently Implemented**:
   - Pattern-based extraction processor (`pattern_extraction_processor.py`)
   - Optimized extraction pipeline (`optimized_pipeline.py`)
   - Mistral OCR integration (`mistral_ocr_processor.py`)
   - Result consolidation mechanism (`result_consolidator.py`)
   - Full document classifier integration with optimized pipeline
   - Lightweight LLM integration (`lightweight_llm_processor.py`)
   - Cross-stream verification for enhanced accuracy
   - Worker pool architecture for parallel processing (`worker_pool_manager.py`)
   - Priority queue management with document prioritization
   - State management with checkpoint/recovery system
   - Comprehensive monitoring and logging system
   - API rate limiting with token bucket algorithm
   - Real-time processing dashboard (`dashboard_server.py`)
   - Document processing visualization with detailed metrics
   - Worker status monitoring with activity tracking
   - API usage tracking visualization with cost monitoring
   - Alerting system for processing issues and bottlenecks

4. **Recently Implemented**:
   - Worker pool integration with optimized pipeline
   - Dashboard integration with optimized pipeline 
   - run_pipeline.sh script for easy execution
   - Command-line options for worker pool configuration
   - Comprehensive validation system integration testing
   - Automated test framework for validation with enhanced extraction
   - Performance benchmarking for validation system
   - Enhanced extraction system testing and refinement
   - Fixed critical BytesIO usage error in enhanced extraction
   - Improved robustness of extraction processing
   
5. **In Progress**:
   - Expanding test coverage with larger document volumes
   - Analytics and visualization enhancements
   - Year-over-year comparison for financial metrics
   - Outlier detection for unusual cost patterns

## Key Files Overview

1. **Document Processing**:
   - `document_classifier.py` - Classifies documents by type
   - `pattern_extraction_processor.py` - Pattern-based extraction for native PDFs
   - `mistral_ocr_processor.py` - OCR extraction for scanned documents
   - `enhanced_tradgarden_processor_v2.py` - Enhanced extraction for rich data

2. **Pipeline Architecture**:
   - `optimized_pipeline.py` - Multi-stream extraction pipeline
   - `process_intelligent.py` - Intelligent processing orchestration

3. **Validation & Reporting**:
   - `validation_system.py` - Human-in-the-loop validation
   - `optimized_report.py` - Consolidated report generation

4. **Testing**:
   - `test_pattern_extraction.py` - Tests pattern-based extraction
   - `test_mistral_ocr.py` - Tests Mistral OCR integration
   - `test_optimized_pipeline.py` - Tests the full pipeline

## Current Focus

The current focus is on expanding test coverage and enhancing analytics:
1. Expanding document test coverage with a larger benchmark dataset
2. Implementing year-over-year comparison for financial metrics
3. Creating outlier detection for unusual cost patterns
4. Developing benchmarking against similar properties
5. Building interactive dashboard for key financial indicators

## Next Steps

1. Expand document test coverage with a larger benchmark dataset
2. Implement year-over-year comparison for financial metrics
3. Create outlier detection for unusual cost patterns
4. Develop benchmarking against similar properties
5. Build interactive dashboard for key financial indicators
6. Implement performance optimization for large-scale processing
7. Create comprehensive visualization system for financial trends

## Recommended Start Prompt

When restarting or after a `/compact` command, use the following start prompt:

```
Help me continue implementing the ZeldaLink optimized extraction pipeline. Please:

1. First review REINCARNATION_PROMPT.md to understand the current system state
2. Then check OPTIMIZED_EXTRACTION_PIPELINE.md to see implementation status and next tasks
3. Look at the most recent implementations (worker_pool_manager.py and dashboard_server.py)
4. Focus on integrating the worker pool architecture with the optimized pipeline
5. Suggest specific next steps to implement based on the documentation

I want to focus on integrating the worker pool architecture with the optimized extraction pipeline. We've completed the worker pool implementation and real-time dashboard development. Now we need to update optimized_pipeline.py to use worker_pool_manager.py for parallelization, implement command-line options for worker pool configuration, and create comprehensive end-to-end tests for the integrated system. How should we approach this integration, and what specific code changes are needed?
```

This prompt will quickly orient you to the current system state and focus your attention on the next implementation tasks.

## Documentation Standards

Before making any changes to the ZeldaLink system, review MASTER_README.md and DOCUMENTATION_GUIDE.md to understand documentation standards.

All significant changes require documentation updates:
1. Update CLAUDE.md with new features and "Recently Completed" section
2. Create or update component-specific documentation
3. Document according to guidelines in DOCUMENTATION_GUIDE.md
4. Update documentation in the same commit as code changes

Remember these principles:
- Undocumented code is considered incomplete
- Document WHY, not just WHAT or HOW
- Add confidence scores to all extracted fields for validation
- Update documentation examples with real working commands
- Include API usage patterns and rate limiting strategies for external services
- Document resource requirements for large-scale processing tasks

## Testing Recommendations

Before completing work on a component:
1. Run the corresponding test script (e.g., `python test_pattern_extraction.py`)
2. Test integration with the full pipeline using `python test_optimized_pipeline.py`
3. Verify that confidence scores are properly calculated for extracted data
4. Check that documentation examples use real working commands
5. Update all relevant documentation

## Documentation Sync Warning

⚠️ **CRITICAL**: When completing a phase or major component, you MUST synchronize the following sections across all documentation files:
1. "Next Steps" in CLAUDE.md
2. "Current Focus" in REINCARNATION_PROMPT.md
3. "Next Steps" in REINCARNATION_PROMPT.md
4. "Current Priorities" in MASTER_README.md
5. Implementation status in OPTIMIZED_EXTRACTION_PIPELINE.md

Failure to do this has previously led to confusion and implementation errors!

## Last Updated

2025-03-11 - Updated to reflect completion of enhanced extraction system testing and refinement