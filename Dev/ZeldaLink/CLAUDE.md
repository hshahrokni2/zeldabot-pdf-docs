# Claude Instructions: ZeldaLink Swedish HOA Report Extraction System

## Project Overview
ZeldaLink is a specialized data extraction system for Swedish "Bostadsrättsförening" (BRF) annual reports. These are financial and administrative reports from Housing Associations that contain critical financial metrics, property information, and maintenance details. These reports:

- Follow semi-standardized formats but vary significantly between associations
- Contain important structured data (costs, revenues, property metrics) embedded in unstructured text
- Include financial statements, maintenance history, and property details
- Are written in Swedish with specialized financial and property terminology

The system uses an advanced multi-tiered extraction approach:
1. Pattern-based extraction: Primary approach using regex, NLP, and heuristics tuned for Swedish financial text
2. LLM-enhanced extraction: Secondary approach using Qwen VL Max to interpret ambiguous or complex segments
3. OCR-based extraction: Fallback for documents with encoding issues or poor text extraction
4. Vision-based extraction: Uses Qwen VL Max vision capabilities to extract data directly from document images
5. Combined OCR+Vision approach: Merges results from both OCR and vision-based extraction for best results
6. Document-specific processing: Custom extraction for known document types with unique characteristics
7. Hybrid pipeline: Merges results from multiple extraction methods, prioritizing the most reliable data

## Current Status

We're working with three test documents located in the raw_docs folder:
1. **BRF Sailor** (`raw_docs/282782_årsredovisning__brf_sailor.pdf`) - Successfully extracted using sailor_specific_processor.py 
2. **BRF Forma** (`raw_docs/283727_årsredovisning__brf_forma_porslinsfabriken.pdf`) - Successfully extracted with standard processing
3. **BRF Trädgården** (`raw_docs/282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf`) - Successfully processed with our enhanced OCR+Vision approach

Our automated document classifier correctly identifies:
- BRF Sailor as a "special_format" document requiring document-specific processing
- BRF Forma as a "standard" document suitable for standard extraction
- BRF Trädgården as a "scanned" document requiring OCR+Vision approach

### Recently Completed
1. ✅ **Implemented OCR+Vision LLM approach** for the BRF Trädgården document
2. ✅ **Created test scripts** to verify API connectivity: test_api.py and test_vision_api.py
3. ✅ **Added automated comparison** of different extraction methods
4. ✅ **Fixed Qwen VL Max message format** to work properly with both text and vision capabilities
5. ✅ **Created comprehensive documentation** in OCR_VISION_README.md
6. ✅ **Implemented automated document classification** with `document_classifier.py`
7. ✅ **Created intelligent processing pipeline** with `process_intelligent.py`
8. ✅ **Developed enhanced Trädgården processor** with advanced OCR+Vision techniques
9. ✅ **Implemented human-in-the-loop validation system** with `validation_system.py`
10. ✅ **Enhanced validation interface** with rejection and commenting capabilities
11. ✅ **Developed comprehensive extraction strategy** for richer document content
12. ✅ **Implemented enhanced_tradgarden_processor_v2.py** with rich information extraction capabilities:
    - Contextual information extraction (board members, associations)
    - Rich text blocks for maintaining context around numerical values
    - Page-type detection with specialized extraction prompts
    - Multi-page synthesis for comprehensive document understanding
    - Extended JSON schema with governance and context information
    - Comprehensive documentation in ENHANCED_TRADGARDEN_V2_README.md
13. ✅ **Fixed validation system integration for rich extraction data**:
    - Updated validation system to handle complex nested data structures from enhanced extraction
    - Added support for all categories in enhanced data schema (governance, context, maintenance)
    - Implemented improved field type recognition for rich contextual information
    - Created test script to verify integration between enhanced extraction and validation
    - Added comprehensive documentation in VALIDATION_INTEGRATION_README.md
14. ✅ **Designed optimized extraction pipeline for large-scale processing**:
    - Created comprehensive strategy for processing 30,000+ documents
    - Designed multi-stream architecture based on document type
    - Integrated Mistral OCR as primary OCR solution
    - Developed model selection criteria for different document types
    - Created detailed implementation plan with timeline and resource allocation
    - Added comprehensive documentation in OPTIMIZED_EXTRACTION_PIPELINE.md
15. ✅ **Implemented first phase of the optimized extraction pipeline**:
    - Integrated Mistral OCR for efficient document processing
    - Created comprehensive pattern-based extraction for native PDFs
    - Implemented specialized Swedish-specific text processing
    - Developed multi-stream document routing in the pipeline
    - Added confidence scoring for extraction quality assessment
    - Updated OPTIMIZED_EXTRACTION_PIPELINE.md with implementation status
16. ✅ **Completed pattern-based extraction implementation**:
    - Created robust pattern-based extraction processor (pattern_extraction_processor.py)
    - Implemented Swedish-specific text post-processing for improved accuracy
    - Added property information extraction with specialized patterns
    - Implemented financial data extraction with context-aware patterns
    - Integrated governance and notes extraction capabilities
    - Added comprehensive confidence scoring for all extracted fields
17. ✅ **Implemented pipeline integration and processing orchestration**:
    - Updated optimized_pipeline.py with multi-stream processing capabilities
    - Added document type classification and stream selection
    - Implemented parallel processing with configurable worker count
    - Created metadata tracking and batch reporting system
    - Added error handling and processing statistics
    - Integrated pattern-based extraction with the optimized pipeline
18. ✅ **Enhanced detailed financial data extraction system**:
    - Implemented comprehensive Swedish financial cost category extraction
    - Added specialized patterns for extracting detailed subcategory costs
    - Created structured cost hierarchy with 12 main categories and 80+ subcategories
    - Implemented table extraction for capturing tabular financial data
    - Enhanced confidence scoring for detailed cost categories
    - Integrated with human-in-the-loop validation system for field correction
    - Added machine learning feedback loop connection for continuous improvement
19. ✅ **Implemented result consolidation mechanism for multi-stream processing**:
    - Created robust result_consolidator.py for merging extraction results from multiple streams
    - Implemented confidence-based field selection for optimal data quality
    - Added cross-stream verification to improve confidence in extracted data
    - Created priority-based stream selection for cases with conflicting data
    - Implemented detailed metadata tracking for extraction provenance
    - Added support for numerical value comparison with tolerance thresholds
    - Created comprehensive test script for validation (test_result_consolidation.py)
    - Added integration with optimized_pipeline.py for automatic consolidation
    - Created detailed documentation in RESULT_CONSOLIDATION_README.md
20. ✅ **Integrated full document classifier with optimized pipeline**:
    - Implemented document_classifier.py integration in optimized_pipeline.py
    - Added automatic document type detection with feature extraction
    - Created intelligent stream routing based on document features
    - Added detection of scanned documents, encoding issues, and special formats
    - Implemented known format database for improved performance
    - Created graceful fallback to basic classification when needed
    - Built comprehensive test script (test_document_classifier_integration.py)
    - Updated documentation to reflect full integration
    - Completed Phase 3 of the optimized extraction pipeline
21. ✅ **Implemented Lightweight LLM integration for contextual analysis**:
    - Created lightweight_llm_processor.py for context-aware field enhancement
    - Implemented selective enhancement based on confidence thresholds
    - Added field-level verification with document context
    - Created section-level verification for related fields
    - Implemented cross-section consistency verification
    - Added comprehensive caching system for API efficiency
    - Created fallback mechanisms for API unavailability
    - Implemented configurable confidence thresholds
    - Added support for multiple API providers (Mistral, OpenAI)
    - Integrated with optimized_pipeline.py for automatic enhancement
    - Created test_lightweight_llm.py for easy testing
    - Added detailed documentation in LIGHTWEIGHT_LLM_README.md
    - Completed Phase 4 of the optimized extraction pipeline
22. ✅ **Implemented worker pool architecture for parallel document processing**:
    - Created worker_pool_manager.py with comprehensive parallel processing capabilities
    - Implemented priority queue system for document processing with configurable priorities
    - Added state management with checkpoint/recovery for long-running processes
    - Built comprehensive monitoring and logging system for batch processing
    - Implemented API rate limiting with token bucket algorithm
    - Created detailed statistics tracking with worker-level and pool-level metrics
    - Added automatic retry mechanism for failed documents
    - Implemented progress tracking with ETA calculation
    - Created test_worker_pool.py for demonstrating and testing the architecture
    - Updated OPTIMIZED_EXTRACTION_PIPELINE.md with implementation status
    - Completed Phase 5 of the optimized extraction pipeline

23. ✅ **Implemented real-time processing dashboard**:
    - Created dashboard_server.py with comprehensive monitoring capabilities
    - Implemented web-based dashboard for real-time processing status visualization
    - Added worker status monitoring with detailed activity tracking
    - Built document processing visualization with detailed metrics
    - Implemented API usage tracking visualization for cost monitoring
    - Added alerting system for processing issues and bottlenecks
    - Created detailed timeline charts for tracking processing progress
    - Implemented checkpoint-based state recovery for dashboard data
    - Created responsive UI with Bootstrap for optimal viewing experience
    - Added run_dashboard.sh convenience script for easy dashboard launching
    - Integrated with worker pool checkpoints for real-time status updates

24. ✅ **Integrated worker pool with optimized pipeline**:
    - Updated optimized_pipeline.py to use WorkerPoolManager for parallelization
    - Implemented command-line options for worker pool configuration
    - Added dashboard integration with optimized pipeline
    - Created run_pipeline.sh convenience script for easy execution
    - Implemented priority-based document processing
    - Added checkpoint/recovery functionality for interrupted processing
    - Improved error handling and retry mechanisms
    - Integrated API rate limiting for optimal throughput
    - Expanded command-line options for comprehensive configuration
    - Fixed optimized_pipeline.py structural issues for cleaner code

### Key Files and Usage
- enhanced_llm_processor.py - Multi-method extraction with OCR, Vision, and combined approaches
  - Use with: `python enhanced_llm_processor.py --pdf <file> --combined`
- document_classifier.py - Automated document classification system
  - Use with: `python document_classifier.py --input <dir> --output <file> --known-formats <db>`
- process_intelligent.py - Intelligent processing pipeline that selects optimal method 
  - Use with: `python process_intelligent.py --input <file/dir> --output-dir <dir>`
- compare_extraction_methods.py - Compare different extraction methods 
  - Use with: `python compare_extraction_methods.py --pdf <file>`
- tradgarden_enhanced_processor.py - Specialized OCR+Vision processor for BRF Trädgården
  - Use with: `python tradgarden_enhanced_processor.py --pdf <file> --output-dir <dir>`
- enhanced_tradgarden_processor_v2.py - Advanced processor with rich information extraction
  - Use with: `python enhanced_tradgarden_processor_v2.py --pdf <file> --output-dir <dir> --doc-format <format>`
- validation_system.py - Human-in-the-loop validation interface (now with enhanced extraction support)
  - Use with: `python validation_system.py --pdf <pdf_file> --json <extracted_json> --output <output_dir>`
- test_integration.py - Test script to verify validation system integration with enhanced data
  - Use with: `python test_integration.py --json <path_to_enhanced_json> --output <test_dir>`
- run_validation.sh - Convenience script for running the validation system with enhanced data
  - Use with: `./run_validation.sh <pdf_file> <json_file> [output_dir]`
- optimized_report.py - Generate consolidated reports
  - Use with: `python optimized_report.py --input-dir <dir> --compare-methods`
- pattern_extraction_processor.py - Pattern-based extraction for native PDF documents
  - Use with: `python pattern_extraction_processor.py --pdf <file> --output <output_file>`
- test_pattern_extraction.py - Test the pattern-based extraction processor
  - Use with: `python test_pattern_extraction.py --pdf <file> --output <output_file>`
- optimized_pipeline.py - Multi-stream extraction pipeline for processing large volumes
  - Use with: `python optimized_pipeline.py --input <input_dir> --output <output_dir> --parallel <workers>`
- test_optimized_pipeline.py - Test the optimized extraction pipeline
  - Use with: `python test_optimized_pipeline.py --input <input_dir> --output <output_dir> --parallel <workers>`
- worker_pool_manager.py - Worker pool architecture for parallel document processing
  - Used by optimized_pipeline.py for efficient large-scale processing
- test_worker_pool.py - Test script for worker pool functionality
  - Use with: `python test_worker_pool.py --input <input_dir> --output <output_dir> --workers <num_workers>`
- dashboard_server.py - Real-time processing dashboard for monitoring extraction pipeline
  - Use with: `python dashboard_server.py --port <port> --checkpoint-dir <dir>`
- run_dashboard.sh - Convenience script for running the dashboard
  - Use with: `./run_dashboard.sh [--port <port>] [--checkpoint-dir <dir>]`
- run_pipeline.sh - Convenience script for running optimized pipeline with dashboard
  - Use with: `./run_pipeline.sh --input <input_dir> --output <output_dir> --workers <num> [--launch-dashboard]`

## Next Steps
1. ✅ **Fix validation system integration for model training**
   - ✅ Fixed validation system interface to properly work with rich extraction data
   - ✅ Enhanced validation system to handle complex nested structures including arrays and objects
   - ✅ Updated field type recognition to better handle rich contextual information
   - ✅ Created test script to verify integration between enhanced extraction and validation
   - ✅ Implemented path processing logic to support navigation through nested JSON structures
   - ✅ Added support for training feedback loop with field rejection, comments, and flags

2. ✅ **Implement optimized extraction pipeline for scale**
   - ✅ Integrated Mistral OCR for efficient document processing
   - ✅ Implemented multi-stream processing based on document type
   - ✅ Created parallelized processing architecture for handling 30,000+ documents
   - ✅ Implemented pattern-based extraction processor
   - ✅ Integrated pattern-based extraction with the optimized pipeline

3. ✅ **Implement parallelization and scaling features**
   - ✅ Created worker pool architecture for parallel document processing (worker_pool_manager.py)
   - ✅ Implemented queue management with priority handling
   - ✅ Added state management for long-running processes
   - ✅ Built monitoring and logging system for batch processing
   - ✅ Implemented checkpoint system for interrupted processing recovery
   - ✅ Created test script for demonstrating worker pool functionality (test_worker_pool.py)
   
4. ✅ **Implement dashboard for real-time processing status**
   - ✅ Created web-based dashboard for real-time processing status (dashboard_server.py)
   - ✅ Implemented document processing visualization with charts
   - ✅ Added worker status monitoring panel with activity tracking
   - ✅ Created API usage tracking visualization for cost monitoring
   - ✅ Implemented alerting system for processing issues and bottlenecks
   - ✅ Added detailed timeline charts for tracking processing progress
   - ✅ Created run_dashboard.sh convenience script for easy dashboard launching

5. ✅ **Integrate worker pool with optimized pipeline**
   - ✅ Updated optimized_pipeline.py to use worker_pool_manager.py for parallelization
   - ✅ Implemented command-line options for worker pool configuration
   - ✅ Added dashboard integration with optimized pipeline
   - ✅ Created run_pipeline.sh convenience script for easy execution
   - ✅ Updated documentation with end-to-end usage examples

6. ✅ **Test and verify validation system integration** 
   - ✅ Created comprehensive validation system integration test script (test_validation_integration.py)
   - ✅ Implemented automated testing for validation with enhanced extraction data
   - ✅ Added simulation of field modifications, rejections and comments for testing
   - ✅ Created performance benchmarking for validation system
   - ✅ Developed run_validation_tests.sh script for easy test execution
   - ✅ Added comprehensive documentation in VALIDATION_TESTING_README.md
   - ✅ Implemented path handling verification for nested structures and arrays

7. ✅ **Test and refine the enhanced extraction system**
   - ✅ Identified and fixed critical BytesIO usage error in enhanced extraction
   - ✅ Created enhanced_tradgarden_processor_fixed.py with improved robustness
   - ✅ Implemented comprehensive test framework for enhanced extraction evaluation
   - ✅ Developed automated verification of extraction quality and field coverage
   - ✅ Added detailed documentation in ENHANCED_EXTRACTION_IMPROVEMENTS.md
   - ✅ Created comprehensive test plan in ENHANCED_EXTRACTION_TEST_PLAN.md
   - ✅ Identified specific optimization opportunities for rich information extraction

8. **Expand document test coverage**
   - Test the rich extraction approach with more scanned documents
   - Compare extraction quality between v1 and v2 processors
   - Create larger benchmark dataset (~100 documents)
   - Conduct comprehensive performance benchmarking

9. **Enhance analytics and visualization**
   - Implement year-over-year comparison for financial metrics
   - Create outlier detection for unusual cost patterns
   - Develop benchmarking against similar properties
   - Build interactive dashboard for key financial indicators

## API Notes
The Qwen VL Max model requires a specific message format:
```python
messages = [
    {
        "role": "user", 
        "content": [
            {"type": "text", "text": "Your prompt text here"},
            # For vision tasks:
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
        ]
    }
]
```

## Technical Architecture

### Data Flow
1. **Input**: PDF annual reports from Swedish HOAs
2. **Processing Pipeline**:
   - Document classification (document_classifier.py)
   - PDF text extraction (PyMuPDF)
   - Optional OCR for scanned documents (if needed)
   - Pattern-based extraction (enhanced_swedish_extraction.py)
   - LLM-based extraction (llm_processor.py)
   - Results merging (hybrid prioritization logic)
3. **Output**: Structured JSON data + consolidated CSV reports

### Component Details

#### document_classifier.py
- Analyzes documents and determines the appropriate extraction method
- Uses text quality, structure analysis, and format detection
- Classifies documents as standard, scanned, encoding_issues, or special_format
- Maintains database of known document formats for faster processing
- Implements decision tree for optimal extraction method selection

#### process_intelligent.py
- Orchestrates document processing based on classification
- Routes documents to appropriate processors
- Manages processing workflow and result handling
- Implements error handling and retry logic
- Generates processing summaries and reports

#### tradgarden_enhanced_processor.py
- Advanced OCR+Vision processor for scanned documents
- Implements sophisticated image preprocessing for better OCR quality
- Creates optimized vision prompts for financial data extraction
- Uses confidence-based merging of OCR and vision results
- Provides detailed extraction quality metrics

#### hoa-report-processor.py
- Core processing orchestration engine
- Implements two-phase pipeline: learning (pattern discovery) and production (extraction)
- Manages PDF parsing with PyMuPDF
- Handles table detection and specialized layout analysis
- Coordinate system for mapping data to original document locations
- Extracts text and sends to appropriate extraction modules

#### enhanced_swedish_extraction.py
- Pattern-based extraction specifically for Swedish financial terminology
- Contains extensive regex patterns for over 40 financial metrics
- Specialized patterns for property details (designation, area, year built)
- Cost categorization with Swedish financial term mapping
- Uses document structure awareness (headings, sections) for context

#### llm_processor.py
- Qwen VL Max API integration via DashScope's OpenAI-compatible API
- API endpoint: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
- Authentication via OpenAI client with API key
- 3-page context window implementation:
  - Processes document in sliding window chunks
  - Each chunk includes previous, current, and next page
  - Maintains context across page boundaries
- Specialized Swedish financial prompts with examples
- Response parsing and JSON structure normalization
- Error handling and retry logic

#### ocr_extract.py
- OCR-based extraction for PDFs with encoding issues or scanned documents
- Converts PDF pages to images and applies Tesseract OCR
- Swedish language configuration for accurate OCR
- Pattern-based extraction from OCR text
- Fallback mechanism for documents with poor text extraction

#### enhanced_llm_processor.py
- Intelligent detection of encoding issues in PDFs
- Automatic selection of appropriate extraction method
- Combines OCR-based extraction with LLM enhancement
- Merges results from multiple extraction methods
- Handles problematic documents gracefully

#### sailor_specific_processor.py
- Custom extraction for the BRF Sailor document format
- Document-specific pattern recognition and data extraction
- Domain knowledge application for consistent data
- Data validation and enhancement with known information

#### optimized_report.py
- Multi-source data prioritization algorithm:
  1. Enhanced extraction (regex/pattern-based)
  2. Hybrid LLM extraction
  3. LLM-only extraction
  4. Standard extraction
- Data quality scoring based on field completeness
- Per-square-meter calculations for cost metrics
- CSV report generation with configurable columns
- Source tracking metadata for extraction audit

### Data Structures

#### JSON Output Schema
The system extracts into a standardized JSON schema:

```json
{
  "property_info": {
    "property_designation": "string",
    "total_area": float,
    "residential_area": float,
    "apartment_count": int,
    "year_built": int,
    "tax_value": float
  },
  "costs": {
    "energy_costs": float,
    "heating_costs": float,
    "water_costs": float,
    /* 25+ additional cost categories */
  },
  "income_statement": {
    "total_revenue": float,
    "total_expenses": float,
    "profit_loss": float,
    "operating_costs": {/* nested cost details */}
  },
  "extraction_metadata": {
    "hybrid_extraction": boolean,
    "llm_chunking_used": boolean,
    "extraction_method": string,
    "confidence_scores": {/* confidence scores for each field */}
  }
}
```

#### CSV Report Structure
- Key financial metrics (revenue, expenses, profit/loss)
- Property details (designation, area, apartment count)
- Normalized cost categories (per sqm, per apartment)
- Source information and extraction quality metrics
- Confidence scores for extracted values

## Current Results Summary
- Successfully extracted BRF Sailor with specialized processor: 12 cost categories, 53 apartments, 3,471 sqm
- Successfully extracted BRF Forma with standard processing
- Successfully extracted BRF Trädgården with enhanced OCR+Vision approach
- Generated consolidated CSV reports with data from all three documents
- Implemented automated document classification that correctly identifies all test documents
- Created intelligent processing pipeline for optimal method selection

## Next Development Phase Priorities
1. **Expand Test Coverage**
   - Test all extraction methods on a larger dataset
   - Create reference "ground truth" data for key financial metrics
   - Calculate accuracy, coverage, and performance metrics

2. **Human-in-the-Loop Validation System**
   - Create comprehensive validation system that optimally leverages human expertise
   - Develop side-by-side view of PDF and extracted data
   - Implement correction interface for fixing extraction errors
   - Add uncertainty flagging to prioritize human review
   - Track correction patterns to identify systematic extraction issues

3. **Enhanced Analytics & Visualization**
   - Year-over-year comparison for financial metrics
   - Outlier detection for unusual cost patterns
   - Benchmarking against similar properties
   - Interactive dashboard for key financial indicators

4. **Performance Optimization**
   - Profile OCR and extraction bottlenecks
   - Implement asynchronous processing for API calls
   - Add batch processing for multi-document extraction
   - Create progress tracking for long-running extractions

## Key Commands & Workflows
- Intelligent processing: `python process_intelligent.py --input <file/dir> --output-dir <dir>`
- Document classification: `python document_classifier.py --input <dir> --output <file>`
- Enhanced Trädgården processing: `python tradgarden_enhanced_processor.py --pdf <file> --output-dir <dir>`
- Generate consolidated report: `python optimized_report.py --input-dir <dir> --per-sqm`
- Compare extraction methods: `python compare_extraction_methods.py --pdf <file>`

## Notes for Claude
- The document classifier automatically selects the optimal extraction method
- The process_intelligent.py script is the main entry point for document processing
- The tradgarden_enhanced_processor.py provides specialized OCR+Vision processing
- Remember that the best approach for scanned documents is OCR+Vision LLM
- The human-in-the-loop validation system (validation_system.py) is integrated with pattern-based extraction
- The extraction_trainer.py module provides machine learning feedback for continuous improvement
- Confidence scores are crucial for prioritizing fields in the validation system
- The comprehensive Swedish cost extraction system includes 12 categories and 80+ subcategories

## Documentation Maintenance Warning

⚠️ **CRITICAL**: When completing a phase or major component, you MUST synchronize "Next Steps" sections across all documentation files (CLAUDE.md, REINCARNATION_PROMPT.md, MASTER_README.md, and OPTIMIZED_EXTRACTION_PIPELINE.md). Failure to do this has previously led to confusion and implementation errors.

## Last Updated
2025-03-11 - Updated to reflect completion of enhanced extraction system testing and refinement