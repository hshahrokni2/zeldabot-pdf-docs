# ZeldaLink Project Quick Reference Guide

## ⚠️ AFTER CONTEXT LOSS ⚠️
When Claude loses context, simply tell Claude:
```
Read /Users/hosseins/Dev/ZeldaLink/STATE_SNAPSHOT.md
```

## Project Overview
ZeldaLink is a specialized extraction system for Swedish housing association (Bostadsrättsförening or BRF) annual reports. It extracts financial data, property information, and governance details from PDF documents, handling Swedish-specific formatting challenges like space-separated thousands (1 234,56 kr).

## Key Command Reference

### Running the Integration Pipeline
```bash
# Test mode (no API keys required)
export ZELDALINK_TEST_MODE=true
python src/core/integrated_extraction.py --pdf raw_docs/your_document.pdf --output test_results/output.json

# Production mode (requires API keys)
export ZELDALINK_TEST_MODE=false
export MISTRAL_API_KEY=your_api_key_here
python src/core/integrated_extraction.py --pdf raw_docs/your_document.pdf --output test_results/output.json
```

### Claude Direct Extraction (No API Key Required)
```bash
# Generate the script to run Claude Code
./claude_direct_extraction.py --pdf raw_docs/your_document.pdf --output test_results/direct_output.json

# Then run the generated script manually
bash test_results/run_claude_extraction_*.sh
```

### Running Benchmarks
```bash
# API-based benchmarking
./run_enhanced_benchmark.sh

# Claude Direct benchmarking (no API key required)
./run_claude_direct_benchmark.sh
```

## Directory Structure
- `/src/` - Source code
  - `/src/core/` - Core extraction pipeline
  - `/src/utils/` - Utility modules (including Swedish normalization)
  - `/src/validation/` - Validation modules
  - `/src/ocr/` - OCR and vision processing
  - `/src/tables/` - Table extraction and processing
- `/docs/` - Documentation files
  - `/docs/core/` - Main project documentation
- `/benchmarks/` - Benchmarking system and test data
  - `/benchmarks/manual_extraction/` - Ground truth data
- `/raw_docs/` - Test documents
- `/test_results/` - Output from extraction pipeline
- `/direct_results/` - Output from Claude direct extraction
- `/enhanced_results/` - Output from enhanced extraction
- `/scripts/` - Shell scripts for running components

## Key Files
- **Main Documentation**: `MASTER_README.md`, `README.md`
- **Implementation Status**: `FINAL_HANDOVER.md`, `CURRENT_SESSION_SUMMARY.md`
- **Core Pipeline**: `src/core/integrated_extraction.py`
- **Swedish Handling**: `src/utils/swedish_character_normalization.py`
- **Claude Direct**: `claude_direct_extraction.py`, `run_claude_direct_benchmark.sh`
- **API-Based Extraction**: `enhanced_extraction_benchmark.py`, `run_enhanced_benchmark.sh`

## Import Conventions
Always use absolute imports starting with `src`:

```python
# Swedish normalization
from src.utils.swedish_character_normalization import normalize_swedish_text, normalize_swedish_financial_terms

# Validation modules
from src.validation.integrate_validation import integrate_validation

# Core modules
from src.core.pattern_extraction_processor import PatternExtractionProcessor
from src.core.integrated_extraction import run_pattern_extraction

# OCR modules
from src.ocr.mistral_ocr_processor import MistralOCRProcessor
from src.ocr.vision_extract import MistralExtractor
```

## Test Documents
- `raw_docs/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf`
- `raw_docs/282782_årsredovisning__brf_sailor.pdf`
- `raw_docs/283727_årsredovisning__brf_forma_porslinsfabriken.pdf`

## Extraction Approaches
1. **Test Mode**: Generates synthetic data for testing without API calls
2. **API-Based**: Uses the integration pipeline with API calls to Claude/Mistral
3. **Claude Direct**: Uses Claude Code directly in the terminal (no API key needed)

## Swedish Number Format Handling
```python
def normalize_number(text: str):
    # Remove spaces (used as thousand separators in Swedish)
    text = text.replace(" ", "")
    # Replace comma with period for decimal point
    text = text.replace(",", ".")
    # Convert to numeric value
    return float(text)
```

## Docker Support
```bash
# Build and run with Docker Compose
docker-compose up -d

# Run in container
docker-compose exec zeldalink python src/core/integrated_extraction.py --pdf raw_docs/your_document.pdf --output test_results/output.json
```

## Troubleshooting
- **Import Errors**: Check if you're using absolute paths from `src/`
- **API Errors**: Check API key format and validity. Should start with `sk-ant-` for Anthropic
- **Mistral API Issues**: Ensure mistralai==1.6.0 is installed. See `MISTRAL_INTEGRATION.md`
- **PDF Processing**: Ensure PyMuPDF is installed for PDF handling
- **Swedish Character Issues**: Use the normalization functions in `src/utils/`

## Known Limitations
- Test mode generates synthetic data that doesn't match ground truth
- Swedish pattern matching needs improvements for better accuracy
- Performance varies depending on document quality and structure