# Mistral OCR Implementation Next Steps

## Current Status

The Mistral OCR implementation is now working successfully with the following components:

1. `mistral_ocr_client_fixed.py` - Core implementation using Mistral's official SDK
2. `run_mistral_sdk.sh` - Shell script wrapper for easy execution
3. `schema_v2.json` - Enhanced schema with confidence tracking and source references

We have successfully processed three Swedish BRF annual reports with OCR:
- BRF Trädgården (282645)
- BRF Sailor (282782)
- BRF Forma (283727)

## Next Implementation Steps

### 1. Implement Extraction Module - High Priority

Create a new module called `mistral_extraction_processor.py` that will:
- Take the OCR text from Mistral OCR as input
- Extract structured data according to schema_v2.json
- Include confidence scores for each extracted field
- Track source page/paragraph references
- Handle Swedish-specific number formats correctly

```python
# Example pattern for extraction module
class MistralExtractionProcessor:
    def __init__(self, ocr_json_path, schema_path='schema_v2.json'):
        self.ocr_data = self._load_ocr_data(ocr_json_path)
        self.schema = self._load_schema(schema_path)
        self.results = self._initialize_result_structure()
        
    def process(self):
        """Process OCR data and extract structured information"""
        # Extract organization info
        self._extract_organization_info()
        # Extract property details
        self._extract_property_details()
        # Extract financial report
        self._extract_financial_report()
        # Process tables
        self._extract_tables()
        # Extract board information
        self._extract_board_info()
        # Calculate confidence metrics
        self._calculate_confidence_metrics()
        return self.results
        
    def _extract_organization_info(self):
        """Extract organization name, number, etc."""
        # Implementation with regex and pattern matching
        pass
        
    # Additional extraction methods
```

### 2. Create Confidence Scoring System - Medium Priority

Develop a confidence scoring algorithm that:
- Assigns confidence scores based on pattern match quality
- Weights fields by importance
- Handles multiple extraction methods (regex, LLM)
- Provides overall document extraction confidence

```python
def calculate_confidence(extracted_value, context, field_type):
    """Calculate confidence score for an extracted field
    
    Args:
        extracted_value: The extracted value
        context: The text context around the extraction
        field_type: Type of field (text, number, date, etc.)
        
    Returns:
        Float confidence score between 0.0 and 1.0
    """
    base_confidence = 0.0
    
    # Check for empty values
    if not extracted_value:
        return 0.0
        
    # Apply field-specific checks
    if field_type == "number":
        # Higher confidence for properly formatted numbers
        if re.match(r'^\d{1,3}(?: \d{3})*(?:,\d{2})?$', extracted_value):
            base_confidence += 0.4
    elif field_type == "organization_number":
        # Higher confidence for standard org number format
        if re.match(r'^\d{6}-\d{4}$', extracted_value):
            base_confidence += 0.5
    
    # Context-based confidence boost
    if relevant_context_words(context, field_type):
        base_confidence += 0.3
        
    # Cap at 1.0
    return min(base_confidence, 1.0)
```

### 3. Swedish Number Format Handling - Medium Priority

Implement Swedish-specific normalization for financial data:
- Convert "1 234,56 kr" format to 1234.56
- Handle SEK currency indicators
- Process percentage values
- Document conversion in metadata

```python
def normalize_swedish_number(text):
    """Convert Swedish formatted numbers to standard float values
    
    Args:
        text: String containing Swedish formatted number (e.g. "1 234,56 kr")
        
    Returns:
        Float value
    """
    # Remove currency indicators
    text = re.sub(r'(?:kr|SEK|:-)', '', text).strip()
    
    # Remove spaces (used as thousand separators)
    text = text.replace(" ", "")
    
    # Replace comma with period for decimal point
    text = text.replace(",", ".")
    
    # Convert to numeric value
    try:
        return float(text)
    except ValueError:
        return None
```

### 4. Hybrid Extraction Approach - Medium Priority

Implement a hybrid approach that combines:
- Pattern-based extraction for known formats
- LLM-based extraction for complex or variable formats
- Confidence-based field selection
- Fallback mechanisms for low-confidence extractions

### 5. Testing and Evaluation - High Priority

Create a benchmark test suite to:
- Compare extraction results against ground truth
- Calculate accuracy metrics per field
- Measure overall extraction quality
- Track improvements across versions

### 6. Integration with Main Pipeline - Low Priority

Once stable, integrate with the main ZeldaLink pipeline:
- Replace the current OCR text extraction
- Update the schema handling
- Implement confidence tracking throughout the pipeline
- Create validation steps for uncertain fields

## Resources Needed

1. Access to test documents
2. Mistral API key with sufficient quota
3. Ground truth data for comparison
4. Swedish financial terminology list

## Timeline

1. **Week 1**: Implement basic extraction module
2. **Week 2**: Create confidence scoring and Swedish handling
3. **Week 3**: Test against all document types and refine
4. **Week 4**: Integrate with main pipeline

## Next Immediate Tasks

1. Create `mistral_extraction_processor.py`
2. Implement organization info extraction
3. Implement financial data extraction
4. Test with BRF Sailor document
5. Compare results with ground truth data