# ZeldaLink Optimized Extraction Pipeline

## Overview

This document outlines a comprehensive strategy for optimizing the ZeldaLink extraction system to efficiently process large document volumes (30,000+) while prioritizing accuracy. The system uses a tiered approach combining specialized OCR technology, vision models, and pattern-based extraction.

## System Requirements

- **Document Volume**: 30,000 Swedish Housing Association (BRF) annual reports
- **Document Distribution**: 25% scanned documents, 75% native PDFs
- **Primary Objective**: Maximum extraction accuracy
- **Timeline**: Complete processing within 1 week
- **Infrastructure**: Local machine with sufficient processing power
- **Available Technologies**:
  - Mistral OCR API
  - Qwen VL Max (vision model)
  - Pattern-based extraction
  - PyMuPDF (for text extraction)

## Architecture Overview

```
                           ┌─────────────────────┐
                           │  Document Classifier │
                           └──────────┬──────────┘
                                      │
                                      ▼
           ┌───────────────────────────────────────────────┐
           │            Document Type Detection            │
           └───────────────────────────────────────────────┘
                  │               │                │
                  ▼               ▼                ▼
    ┌────────────────────┐ ┌─────────────┐ ┌───────────────────┐
    │   Native PDFs      │ │Scanned PDFs │ │Special Format PDFs│
    └──────────┬─────────┘ └──────┬──────┘ └─────────┬─────────┘
               │                  │                  │
               ▼                  ▼                  ▼
    ┌────────────────────┐ ┌─────────────┐ ┌───────────────────┐
    │PyMuPDF + Patterns  │ │ Mistral OCR │ │Format-Specific    │
    │Text Extraction     │ │             │ │Processors         │
    └──────────┬─────────┘ └──────┬──────┘ └─────────┬─────────┘
               │                  │                  │
               ▼                  ▼                  ▼
    ┌────────────────────┐ ┌─────────────┐ ┌───────────────────┐
    │Lightweight LLM     │ │Vision Model │ │Specialized        │
    │(Context Analysis)  │ │(Complex     │ │Extraction Rules   │
    │                    │ │Elements)    │ │                   │
    └──────────┬─────────┘ └──────┬──────┘ └─────────┬─────────┘
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │   Result Consolidation  │
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │   Validation System     │
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │    Optimized Report     │
                     └─────────────────────────┘
```

## Processing Pipeline

### 1. Document Classification

- **Input**: Raw PDF documents
- **Process**:
  - Enhanced document classifier to categorize as:
    - Native PDF (75% of documents)
    - Scanned document (25% of documents)
    - Special format document (previously identified formats)
  - Page-level classification within each document
- **Output**: Documents with classification metadata

### 2. Processing Streams

#### Stream A: Native PDFs (75% of documents)

1. **Text Extraction**
   - Use PyMuPDF for direct text extraction
   - Apply pattern-based extraction for structured data
   - Implement regex-based field identification for Swedish financial terms

2. **Contextual Analysis**
   - Use lightweight LLM (4o-mini or similar) to:
     - Resolve ambiguities in extracted data
     - Provide context for numerical values
     - Verify extraction quality

3. **Visual Element Extraction**
   - Identify pages with charts, tables, or complex layouts
   - Selectively apply Mistral OCR for tables (96.12% accuracy on tables)
   - Resort to Qwen VL Max only for complex visual elements

#### Stream B: Scanned Documents (25% of documents)

1. **Full Document OCR**
   - Apply Mistral OCR to extract text and structure (98.96% accuracy on scanned docs)
   - Generate structured JSON output with key fields

2. **Complex Element Analysis**
   - Identify financial tables and complex layouts
   - Apply Qwen VL Max for visual verification of critical financial data
   - Compare OCR and vision results for higher confidence

#### Stream C: Special Format Documents

1. **Format-Specific Processing**
   - Apply document-specific processors (e.g., sailor_specific_processor.py)
   - Use templates for known document structures
   - Extract using specialized rules

### 3. Result Consolidation

- Merge results from multiple processing streams based on confidence scores
- Implement priority-based stream selection for conflicting data
- Apply cross-stream verification to improve confidence in extracted data
- Track extraction provenance through detailed metadata
- Support numerical value comparison with tolerance thresholds
- Flag inconsistencies and low-confidence fields for human validation
- Generate comprehensive consolidated JSON output

The result consolidation system uses the following processes:

1. **Stream Prioritization**: Default priorities (higher = more reliable)
   - Format-specific extraction (95)
   - Hybrid extraction approaches (90)
   - Pattern-based extraction (80)
   - Vision-based extraction (70)
   - OCR-based extraction (60)

2. **Confidence-Based Selection**: 
   - Fields with confidence scores above a configurable threshold (default: 50%)
   - For each field, select the value with highest confidence × priority score
   - Record source stream and confidence score in metadata

3. **Cross-Stream Verification**:
   - Compare field values across different streams to identify matches
   - Increase confidence for fields verified across multiple streams
   - Apply tolerance thresholds for numerical comparisons:
     - 5% relative difference for large values (>100)
     - 2 units absolute difference for small values

4. **Consolidated Output Format**:
   - Standard document structure with all sections
   - Field-level provenance tracking (which stream provided each value)
   - Confidence scores for all extracted fields
   - Cross-verification status for each field

### 4. Validation System Integration

- Route processed documents to enhanced validation system
- Prioritize validation based on confidence scores
- Focus human validation on critical financial fields

## Implementation Status

### Phase 1: Mistral OCR Integration (COMPLETED)

1. **API Integration**
   - Implemented Mistral OCR client in Python (`mistral_ocr_processor.py`)
   - Set up authentication and error handling with retry mechanism
   - Created batching mechanism for efficient API usage

2. **OCR Processing Module**
   - Built OCR processor class with structured data extraction capabilities
   - Implemented page selection for partial processing
   - Created structured output parser for Swedish financial data

3. **Benchmark Testing**
   - Created test script (`test_mistral_ocr.py`) for validation
   - Verified functionality with sample documents
   - Integrated with optimized pipeline architecture

### Phase 2: Pattern-Based Extraction (COMPLETED)

1. **Core Extraction Engine**
   - Implemented specialized pattern-based extraction processor (`pattern_extraction_processor.py`)
   - Created comprehensive regex patterns for Swedish financial terms
   - Built Swedish-specific post-processing for improved extraction accuracy
   
2. **Data Extraction Components**
   - Implemented property information extraction
   - Added comprehensive cost category extraction with 12 main categories and 80+ subcategories
   - Created specialized Swedish financial pattern matching for detailed cost extraction
   - Added table extraction capabilities for capturing structured financial data
   - Created income statement extraction capabilities
   - Added governance information extraction
   
3. **Test and Validation**
   - Created test script for pattern-based extraction (`test_pattern_extraction.py`)
   - Added comprehensive confidence scoring for all extracted fields
   - Implemented field-level confidence scoring for detailed cost categories
   - Integrated with human-in-the-loop validation system for field correction and feedback
   - Connected with machine learning training loop for continuous improvement
   - Implemented caching for performance optimization

### Phase 3: Pipeline Integration (PROGRESS: 100%)

1. **Multi-Stream Integration**
   - ✅ Integrated pattern-based extraction with optimized pipeline
   - ✅ Updated _process_native_pdf method to use pattern extraction
   - ✅ Implemented processor initialization with proper error handling
   - ✅ Implemented initial document type detection (basic) 
   - ✅ Added integration with full document classifier
   - ✅ Implemented automatic document type detection with feature extraction
   - ✅ Added known format database for performance optimization
   - ✅ Created graceful fallback to basic classification when needed

2. **Workflow Orchestration**
   - ✅ Enable stream selection based on document type
   - ✅ Update document metadata with extraction results
   - ✅ Implemented parallel processing with configurable worker count
   - ✅ Created batch processing and reporting system
   - ✅ Implemented result consolidation with result_consolidator.py
   - ✅ Added cross-stream verification with confidence boosting
   - ✅ Implemented priority-based stream selection for conflicting data
   - ✅ Added field-level provenance tracking and metadata
   - ✅ Created intelligent stream routing based on document features

3. **Testing Infrastructure**
   - ✅ Created dedicated test scripts for each processor
   - ✅ Implemented test_optimized_pipeline.py for pipeline testing
   - ✅ Added basic processing metrics and statistics
   - ✅ Implemented test_result_consolidation.py for testing consolidation
   - ✅ Created test_document_classifier_integration.py for classifier testing
   - 🔄 Add comprehensive performance benchmarking

### Phase 4: Lightweight LLM Integration (PROGRESS: 100%)

1. **Model Integration**
   - ✅ Set up Mistral 7B Instruct model for context analysis
   - ✅ Created specialized prompts for financial document understanding
   - ✅ Implemented efficient prompt design for Swedish financial texts
   - ✅ Added support for multiple API providers (Mistral AI, OpenAI)
   - ✅ Built lightweight_llm_processor.py for core functionality

2. **Context Analysis**
   - ✅ Implemented context-aware analysis of extracted data
   - ✅ Created field verification with document context for ambiguous data
   - ✅ Added section verification for related fields
   - ✅ Developed cross-section consistency verification
   - ✅ Implemented specialized context extraction for different data types

3. **Performance Optimization**
   - ✅ Implemented selective processing based on confidence scores
   - ✅ Created comprehensive caching system for LLM responses
   - ✅ Added configurable cache expiry for long-running processes
   - ✅ Implemented fallback mechanisms for API unavailability
   - ✅ Optimized token usage with targeted context extraction

### Phase 5: Parallelization & Scaling (PROGRESS: 100%)

1. **Worker Pool Architecture**
   - ✅ Implemented WorkerPoolManager for parallel document processing
   - ✅ Created multi-process architecture with configurable worker count
   - ✅ Added comprehensive monitoring and logging system
   - ✅ Implemented API rate limiting with token bucket algorithm
   - ✅ Created worker statistics tracking with detailed metrics

2. **Queue Management**
   - ✅ Built priority queue system for document processing
   - ✅ Implemented document priority based on document type
   - ✅ Created configurable priority levels (High, Medium, Low)
   - ✅ Added progress tracking with detailed statistics
   - ✅ Implemented automatic retry mechanism for failed documents

3. **State Management**
   - ✅ Implemented checkpoint system for long-running processes
   - ✅ Created recovery mechanism for interrupted processing
   - ✅ Added automatic periodic checkpointing with configurable interval
   - ✅ Built work item tracking with comprehensive metadata
   - ✅ Created detailed reporting system with statistics

### Phase 6: Validation & Reporting (PLANNED)

1. **Enhanced Validation Integration**
   - Update validation system for multi-stream results
   - Implement confidence-based field highlighting
   - Create aggregated validation statistics

2. **Processing Dashboard**
   - Build real-time processing status dashboard
   - Implement extraction quality metrics
   - Create processing time analytics

> **Note**: Phases 1 and 2 are complete. Phase 3 is currently in progress, with Phases 4-6 scheduled for future implementation.

## Scaling Considerations

### API Rate Management

- Implement exponential backoff for API rate limits
- Use token bucket algorithm for fair API usage distribution
- Create API call scheduling to maximize throughput

### Resource Allocation

- Allocate 75% of computational resources to pattern-based extraction
- Allocate 20% to Mistral OCR processing
- Reserve 5% for vision model processing of complex elements

### Batch Optimization

- Process documents in batches of 100-500 depending on type
- Group similar documents for efficiency
- Schedule API-intensive tasks during off-peak hours

## Cost Optimization

### Model Usage Strategy

- Minimize vision model usage (most expensive)
- Maximize pattern-based extraction (least expensive)
- Use Mistral OCR as the primary OCR solution (better cost/performance ratio)

### Processing Tiers

Implement a tiered processing strategy:

1. **Tier 1 (All Documents)**
   - Basic pattern-based extraction
   - PyMuPDF text extraction
   - Struct ured field identification

2. **Tier 2 (40% of Documents)**
   - Lightweight LLM for context understanding
   - Mistral OCR for tables and complex text

3. **Tier 3 (5-10% of Documents)**
   - Vision models for visual verification
   - Multi-modal synthesis for difficult cases

## Expected Performance

- **Processing Time**: 5-7 days for 30,000 documents
- **Accuracy**: 
  - 95%+ for native PDFs
  - 90%+ for scanned documents
  - 85%+ for special format documents
- **Field Coverage**: 
  - 40+ financial metrics
  - Complete property details
  - Contextual information

## Integration with Existing ZeldaLink Components

- Maintain compatibility with existing validation system
- Extend document classifier with page-level capabilities
- Enhance intelligent processing pipeline for multi-stream support
- Update optimized report generator for consolidated results

## Monitoring and Evaluation

- Implement continuous accuracy monitoring
- Track API usage and costs
- Measure processing times across document types
- Evaluate field-level extraction accuracy

## Next Steps After Implementation

1. **Continuous Improvement**:
   - Analyze validation patterns to improve extraction
   - Fine-tune model selection based on performance metrics
   - Implement learning system for recurring document formats

2. **Extended Features**:
   - Add year-over-year comparison capabilities
   - Implement outlier detection for unusual financial patterns
   - Develop predictive analytics for maintenance planning

3. **Scaling Beyond 30,000**:
   - Implement distributed processing across multiple machines
   - Develop cloud-based processing option for larger volumes
   - Create incremental processing strategy for continuous document flows

## Appendix A: Model Selection Criteria

| Document Type | Primary Model | Secondary Model | Final Verification |
|---------------|--------------|-----------------|-------------------|
| Native PDF with simple structure | Pattern-based | - | Random sampling |
| Native PDF with complex tables | Pattern-based | Mistral OCR | Field validation |
| Native PDF with graphs/charts | Pattern-based | Qwen VL Max | Human validation |
| Scanned document (text only) | Mistral OCR | - | Field validation |
| Scanned document (with tables) | Mistral OCR | Qwen VL Max | Human validation |
| Special format document | Format-specific | Mistral OCR | Human validation |

## Appendix B: API Configuration

### Mistral OCR Configuration

```python
# Mistral OCR API Setup
import requests

MISTRAL_API_KEY = "bQj5DDdlqjzUuqDtCHCcvy6CLcjqcbwO"
MISTRAL_OCR_ENDPOINT = "https://api.mistral.ai/v1/ocr"

headers = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}

def process_document_ocr(document_path, pages=None):
    """Process document with Mistral OCR API"""
    with open(document_path, "rb") as f:
        document_data = f.read()
        document_base64 = base64.b64encode(document_data).decode()
    
    payload = {
        "model": "mistral-ocr-2503",
        "document": {
            "data": document_base64,
            "type": "application/pdf"
        },
        "pages": pages,
        "include_image_base64": False
    }
    
    response = requests.post(
        MISTRAL_OCR_ENDPOINT,
        headers=headers,
        json=payload
    )
    
    return response.json()
```

### Qwen VL Max Configuration

```python
# Qwen VL Max API Setup
from openai import OpenAI

DASHSCOPE_API_KEY = "your_dashscope_api_key"

client = OpenAI(
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    api_key=DASHSCOPE_API_KEY
)

def process_with_vision(image_base64, prompt):
    """Process image with Qwen VL Max API"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
            ]
        }
    ]
    
    response = client.chat.completions.create(
        model="qwen-vl-max",
        messages=messages,
        temperature=0.1,
        max_tokens=4096
    )
    
    return response.choices[0].message.content
```

## Appendix C: Key Performance Indicators

1. **Processing Efficiency**:
   - Documents per hour
   - API calls per document
   - Processing time per document type

2. **Extraction Quality**:
   - Field coverage percentage
   - Confidence score averages
   - Validation correction rate

3. **Cost Metrics**:
   - Average API cost per document
   - Cost per extraction field
   - Cost reduction compared to vision-only approach

## Last Updated

2025-03-11 - Updated to reflect completion of enhanced extraction system testing and refinement