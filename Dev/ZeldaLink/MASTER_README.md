# ZeldaLink Master Documentation

## Introduction

Welcome to ZeldaLink, a specialized data extraction system for Swedish Housing Association (BRF) annual reports. This document serves as the master reference guide to help you navigate the project's documentation, understand its architecture, and contribute effectively.

## Required Reading

Before working with ZeldaLink, you MUST read these documents:

1. **[DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md)** - Standards for documentation and why it matters
2. **[CLAUDE.md](CLAUDE.md)** - Comprehensive overview of the system architecture and current status
3. **[README.md](README.md)** - Installation and basic usage instructions

## Component-Specific Documentation

Depending on which area you'll be working on, review these detailed component guides:

1. **[HUMAN_IN_THE_LOOP_README.md](HUMAN_IN_THE_LOOP_README.md)** - Human validation system
2. **[OCR_VISION_README.md](OCR_VISION_README.md)** - OCR and vision-based extraction
3. **[DOCUMENT_CLASSIFIER_README.md](DOCUMENT_CLASSIFIER_README.md)** - Document classification system
4. **[ENHANCED_TRADGARDEN_V2_README.md](ENHANCED_TRADGARDEN_V2_README.md)** - Enhanced extraction system
5. **[direct_view/VALIDATION_INTEGRATION_README.md](direct_view/VALIDATION_INTEGRATION_README.md)** - Validation system integration with enhanced extraction
6. **[OPTIMIZED_EXTRACTION_PIPELINE.md](OPTIMIZED_EXTRACTION_PIPELINE.md)** - Optimized large-scale extraction pipeline

## System Architecture

ZeldaLink uses a multi-tiered extraction approach with optimized stream selection:

1. **Document Classification** - Determines document type and optimal processing stream
2. **Multi-Stream Processing** - Routes documents to the appropriate extraction method:
   - **Pattern-based Stream** - For native PDFs (75% of documents)
   - **OCR-based Stream** - For scanned documents (25% of documents)
   - **Format-specific Stream** - For known document formats
3. **Optimized Model Selection**:
   - **Mistral OCR** - Primary OCR solution for scanned documents and tables
   - **Lightweight LLM** - For contextual understanding of extracted text
   - **Qwen VL Max** - For complex visual elements and verification
4. **Human Validation** - For reviewing and correcting uncertain extractions
5. **Parallel Processing** - For efficient handling of large document volumes

This modular architecture allows ZeldaLink to handle a wide variety of document formats while maximizing extraction accuracy.

## Key Workflows

### Large-Scale Processing Workflow

```
optimized_pipeline.py (with parallel workers) → validation_system.py → optimized_report.py
```

### Standard Processing Workflow

```
document_classifier.py → process_intelligent.py → enhanced_llm_processor.py → optimized_report.py
```

### Validation Workflow

Standard extraction:
```
process_intelligent.py → enhanced_llm_processor.py → validation_system.py → optimized_report.py
```

Enhanced extraction with rich data:
```
process_intelligent.py → enhanced_tradgarden_processor_v2.py → run_validation.sh → optimized_report.py
```

### Scanned Document Workflow

```
document_classifier.py → process_intelligent.py → tradgarden_enhanced_processor.py → validation_system.py → optimized_report.py
```

## Getting Started

### Setting Up the Development Environment

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/zeldalink.git
   cd zeldalink
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   python -m spacy download sv_core_news_sm
   ```

3. Set up your API keys in a `.env` file
   ```
   DASHSCOPE_API_KEY=your_dashscope_api_key_here
   MISTRAL_API_KEY=your_mistral_api_key_here
   ```

### Running the System

Process large batches of documents with the optimized pipeline:

```bash
# Using the raw command
python optimized_pipeline.py --input raw_docs/ --output processed_results --parallel 8

# Using the convenience script with dashboard
./run_pipeline.sh --input raw_docs --output processed_results --workers 8 --launch-dashboard
```

Process documents with Mistral OCR:

```bash
python mistral_ocr_processor.py --pdf raw_docs/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf --output ocr_results/
```

Process a document with automatic classification:

```bash
python process_intelligent.py --input raw_docs/283727_årsredovisning__brf_forma_porslinsfabriken.pdf --output-dir processed_docs
```

Use the human validation system with standard extraction:

```bash
python validation_system.py --pdf raw_docs/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf --json output_enhanced/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf_enhanced_processed.json --output validated_results
```

Use the human validation system with enhanced extraction:

```bash
cd direct_view
./run_validation.sh ../raw_docs/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf ../enriched_results/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf_enhanced_tradgarden_v2_results.json ../validated_results
```

Generate consolidated reports:

```bash
python optimized_report.py --input-dir validated_results --per-sqm
```

## Current Development Status

### Recently Completed

- Implemented automated document classification system
- Developed enhanced OCR+Vision processor for scanned documents
- Created intelligent processing pipeline for method selection
- Implemented enhanced extraction with rich contextual information
- Fixed validation system integration for enhanced extraction data
- Added support for training feedback loop in validation system
- Designed optimized extraction pipeline for large-scale processing
- Implemented Mistral OCR integration for efficient text extraction
- Created multi-stream processing architecture for different document types
- Implemented result consolidation mechanism for multi-stream processing
- Integrated full document classifier with optimized pipeline
- Added cross-stream verification with confidence boosting mechanisms
- Implemented lightweight LLM integration for contextual analysis
- Created comprehensive caching system for API efficiency
- Added support for multiple API providers with fallback mechanisms
- Implemented worker pool architecture for parallel document processing
- Created priority queue system for document processing
- Added state management with checkpoint/recovery for long-running processes
- Built comprehensive monitoring and logging system for batch processing
- Implemented API rate limiting with token bucket algorithm
- Created detailed statistics tracking with worker-level and pool-level metrics
- Implemented real-time processing dashboard with visualization capabilities
- Created document processing visualization with detailed metrics
- Added worker status monitoring with activity tracking
- Implemented API usage tracking visualization with cost monitoring
- Added alerting system for processing issues and bottlenecks
- Created detailed timeline charts for tracking processing progress
- Integrated worker pool with optimized pipeline for parallelization
- Created run_pipeline.sh convenience script with dashboard integration
- Added checkpoint/recovery functionality for reliable processing
- Implemented priority-based document processing queue
- Developed comprehensive validation system integration tests
- Created automated test framework for validation with enhanced extraction data
- Implemented simulation of field validations for testing
- Added performance benchmarking for validation system
- Created run_validation_tests.sh script for easy test execution
- Added detailed documentation in VALIDATION_TESTING_README.md
- Fixed critical BytesIO usage error in enhanced extraction
- Created enhanced_tradgarden_processor_fixed.py with improved robustness
- Implemented comprehensive test framework for enhanced extraction evaluation
- Developed automated verification of extraction quality and field coverage
- Added detailed documentation in ENHANCED_EXTRACTION_IMPROVEMENTS.md
- Created comprehensive test plan in ENHANCED_EXTRACTION_TEST_PLAN.md

### Current Priorities

1. Expand test coverage and benchmarking
   - Create larger benchmark dataset (~100 documents)
   - Conduct comprehensive performance benchmarking
   - Optimize parallel processing parameters
   - Fine-tune API rate limiting parameters

2. Enhance analytics and visualization
   - Implement year-over-year comparison for financial metrics
   - Create outlier detection for unusual cost patterns
   - Develop benchmarking against similar properties
   - Build interactive dashboard for key financial indicators

3. Optimize system for production scale
   - Profile and optimize processing bottlenecks
   - Implement efficient processing scheduling
   - Create comprehensive monitoring and alerting
   - Develop incremental processing capabilities

4. Create comprehensive visualization system
   - Implement financial trend visualization
   - Add comparative analysis between HOAs
   - Create cost category breakdown dashboards
   - Develop year-over-year change analysis tools

## Best Practices

1. **Follow the documentation guide** - Keep documentation up-to-date
2. **Utilize the validation system** - For uncertain extractions
3. **Run the document classifier** - To determine optimal extraction method
4. **Compare extraction methods** - When dealing with problematic documents
5. **Use confidence scores** - To identify areas for improvement

## Support

If you encounter issues or have questions, please:

1. Check the existing documentation first
2. Look for similar issues in the issue tracker
3. Create a new issue with detailed reproduction steps
4. Include relevant logs and context

## License

This project is licensed under the MIT License - see the LICENSE file for details.