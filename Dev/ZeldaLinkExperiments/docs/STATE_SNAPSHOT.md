# STATE SNAPSHOT

## Last Updated
2025-03-28 18:00:00

## Current Status
We have successfully implemented the self-learning extraction system with Pydantic models, schema improvement analysis,
and cross-document validation. The system supports multiple LLM providers (Mistral, OpenAI GPT-4, Anthropic Claude) 
and includes schema improvement suggestions with automatic consolidation and implementation recommendations.

The complete extraction pipeline now includes testing on all three BRF documents, collecting and analyzing schema
improvement suggestions, and validating extraction results across documents and models.

We have enhanced the schema based on extraction suggestions and tested these improvements on the Sailor BRF document,
achieving ~90-95% extraction accuracy on structured fields with both Mistral and Claude models.

## Active Tasks
- Testing extraction with year-over-year comparison fields
- Implementing cross-page integration for complex financial data
- Improving error handling for API failures
- Implementing cross-page integration for complex financial data
- Enhancing extraction accuracy based on validation feedback

## Recent Changes
- Enhanced schema with new fields based on extraction suggestions:
  - Added ContactDetails (phone, email, website) to Organization
  - Added commercial_area_sqm to PropertyDetails
  - Added revenue_breakdown and expense_breakdown to IncomeStatement
  - Added loan_amortization_amount and total_debt to FinancialMetrics
- Added year-over-year comparison fields to schema:
  - Added previous_year_revenue, previous_year_expenses, previous_year_net_income to IncomeStatement
  - Added previous_year_revenue_breakdown and previous_year_expense_breakdown to IncomeStatement
  - Added average_interest_rate to FinancialMetrics
- Added "unverified fields guide" to extraction prompts to identify additional potential fields:
  - Property details (renovation year, elevators, parking spaces, energy classification, heating system)
  - Financial metrics (maintenance fund, future budget, debt ratio, interest trends, cash reserves)
  - Governance (annual meetings, external auditors, board meeting frequency, property management)
  - Maintenance planning (plan period, upcoming renovations, completed projects, deferred maintenance)
  - Member information (ownership transfers, fee history, apartment size distribution)
- Updated all extractor prompts (Mistral, GPT-4, Claude) to support new schema fields
- Tested extraction with enhanced schema on Sailor BRF document
- Compared extraction results between Mistral and Claude models
- Identified additional schema improvements for year-over-year comparisons
- Created COMPACTION_GUIDE.md with comprehensive project information

## Post-Compaction Recovery
If you're reading this after a context reset or compaction:
1. Read START.md for critical project information
2. Run `python test_schema_fields.py` to verify schema implementation
3. Check the code and examples in START.md to understand features
4. Run extraction in test mode to verify functionality:
   ```bash
   export ZELDALINK_TEST_MODE=true
   ./run_sailor_extraction.sh
   ```

## Upcoming Work
- Add field-specific extractors for common Swedish table formats
- Implement cross-page integration for complex data across multiple pages
- Improve extraction accuracy for fields with low consistency
- Create a fully automated pipeline for extraction, analysis, and validation
- Implement schema improvement integration process

## Known Issues
- Claude API has JSON parsing issues in extraction (added workaround)
- Need to implement proper error handling for API failures
- Testing with real API keys needed to validate extraction accuracy
- Schema improvements need manual review before integration

## Implementation Details

### Current Working State
- Full Pydantic model implementation based on schema_v2.json
- Multiple LLM providers supported (Mistral, OpenAI GPT-4, Anthropic Claude)
- Schema improvement suggestions capability
- Schema improvement analysis and consolidation
- Cross-document and cross-model validation
- Test mode with mock data for development/testing without API keys
- Comprehensive documentation and reporting

### Full Extraction Pipeline Components
1. **Extraction System**: Core extraction system with Pydantic models
2. **Multi-Document Extraction**: Script to run extraction on all three BRF documents
3. **Schema Improvement Analysis**: Tool to analyze and consolidate schema improvement suggestions
4. **Extraction Validation**: System for cross-document and cross-model validation
5. **Implementation Recommendations**: Automatic generation of implementation code

### Code Patterns to Follow
When implementing the Pydantic models, follow this structure:
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class ConfidenceEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SomeSection(BaseModel):
    field_name: Optional[str] = None
    numeric_field: Optional[float] = None
    confidence: Dict[str, ConfidenceEnum] = Field(default_factory=dict)
```

When implementing extraction with schema improvement, follow this pattern:
```python
def extract_with_improvements(ocr_text, model="mistral-large-latest"):
    """Extract data with schema improvement suggestions."""
    prompt = f"""
    Analyze this text and extract structured data according to the schema.
    Also suggest any data that should be added to the schema.
    
    {ocr_text}
    """
    
    # API call implementation
    # ...
    
    # Process and return results
    return {
        "extraction": extracted_data,
        "schema_improvements": improvement_suggestions
    }
```

### Key Implementation Insights
- The schema needs to capture ALL financial data in the documents
- Having the models suggest schema improvements is core to our approach
- Missing data often includes:
  - Amortization amounts for loans
  - Financial summary data
  - Board member details
- GPT-4 and Mistral Large are most accurate for extraction
- The response format needs to be carefully structured for consistent parsing

### Diagnostic Tips
If the extraction isn't working properly:
1. Check the OCR text quality first
2. Verify prompt formatting is consistent
3. Ensure schema structure matches expected output
4. Check for Swedish number format normalization issues

### Critical Implementation Reminder
DO NOT reinvent approaches for:
- OCR processing (use existing client)
- Schema structure (extend existing schema)
- Extraction prompts (follow established patterns)
- API integration (use existing patterns)