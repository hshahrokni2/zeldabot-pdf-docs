# Enhanced Extraction Test Plan

## Overview

This test plan outlines the steps to verify that the Enhanced Extraction system is working correctly after implementation of API retry logic and Swedish normalization fixes.

## Prerequisites

1. **Environment Setup**:
   ```bash
   # Set either ANTHROPIC_API_KEY or CLAUDE_API_KEY
   export ANTHROPIC_API_KEY=your_api_key_here
   
   # Set to false for real testing (true for simulated data)
   export ZELDALINK_TEST_MODE=false
   ```

2. **Test Data**:
   - Test documents located in `/raw_docs/` directory
   - Primary test cases: BRF Trädgården, BRF Sailor, BRF Forma

## Test Suite

### Test 1: Basic Extraction (without API)

Test the pattern extraction without API calls to verify basic functionality.

```bash
python enhanced_tradgarden_processor_fixed.py --pdf raw_docs/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf --output test_results/tradgarden_pattern_only.json
```

✓ Expected: Should extract basic fields without API calls

### Test 2: Test Mode Extraction

Run with test mode to verify system structure without making real API calls.

```bash
export ZELDALINK_TEST_MODE=true
python src/core/integrated_extraction.py --pdf raw_docs/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf --output test_results/tradgarden_test_mode.json
```

✓ Expected: Should complete without errors, using simulated data

### Test 3: Enhanced Extraction with API

Run full extraction with API calls using retry logic.

```bash
export ZELDALINK_TEST_MODE=false
python enhanced_extraction_benchmark.py --pdf raw_docs/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf --output test_results/tradgarden_enhanced_api.json
```

✓ Expected: Should complete with API calls, with retry for transient errors

### Test 4: Full Benchmark Suite

Run the full benchmark suite on multiple documents.

```bash
./run_enhanced_benchmark.sh
```

✓ Expected: Should process all documents with API calls and generate report

## Verification Checklist

After running tests, verify the following:

### Swedish Normalization
- [ ] Verify numbers with spaces (e.g., "1 234,56") are properly converted to 1234.56
- [ ] Check that decimal commas are properly handled in financial tables

### API Resilience
- [ ] Check logs for API retries
- [ ] Verify successful completion even with occasional API errors
- [ ] Ensure results are consolidated properly across batches

### Data Completeness
- [ ] Property info is correctly extracted
- [ ] Financial data is properly normalized and structured
- [ ] Tables are properly detected and processed
- [ ] Board members are correctly identified

## Comparison with Gold Standard

```bash
python benchmarks/compare_results.py --before pre_consolidation_results.json --after enhanced_results/enhanced_extraction_report.md
```

Expected: Overall accuracy should match or exceed the 96.8% pre-consolidation level

## Troubleshooting

If API errors persist:
1. Check API key configuration
2. Monitor request logs for error details
3. Check for API rate limiting
4. Verify required API headers are sent
5. Try reducing batch sizes