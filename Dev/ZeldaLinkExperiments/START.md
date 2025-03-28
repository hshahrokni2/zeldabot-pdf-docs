# START - ZeldaLink Project Guide

## CURRENT PROJECT STATUS

The ZeldaLink project is a Swedish housing association (BRF) document extraction system that has implemented:

1. **Core Extraction System**
   - Multiple LLM support (Mistral, OpenAI GPT-4, Anthropic Claude)
   - Pydantic models with confidence tracking
   - Schema improvement suggestion capability

2. **Recent Enhancements**
   - Year-over-year comparison fields added to financial statements
   - Average interest rate calculation added to financial metrics
   - Unverified fields detection system for continuous schema improvement

## CRITICAL FILES AND DEPENDENCIES

1. **Core Code Files**
   - `/src/extraction/schema.py` - Pydantic models with year-over-year fields
   - `/src/extraction/extract.py` - Extraction with unverified fields detection
   - `/unverified_fields_guide.py` - Potential fields to watch for
   - `/test_schema_fields.py` - Schema validation test

2. **Module Dependency Map**
   ```
   schema.py ← extract.py ← unverified_fields_guide.py
   ```

## SCHEMA ENHANCEMENTS

```python
# Year-over-year comparison fields in IncomeStatement
previous_year_revenue: Optional[NumberField] = None
previous_year_expenses: Optional[NumberField] = None
previous_year_net_income: Optional[NumberField] = None
previous_year_revenue_breakdown: Optional[RevenueBreakdown] = None
previous_year_expense_breakdown: Optional[ExpenseBreakdown] = None

# Added to FinancialMetrics
average_interest_rate: Optional[NumberField] = None
```

## UNVERIFIED FIELDS DETECTION

We're watching for these categories of fields in documents:
- **Property Details**: renovation year, elevators, parking, energy classification
- **Financial Metrics**: maintenance fund, budget data, debt ratio, liquidity
- **Governance**: annual meetings, auditors, board meeting frequency
- **Maintenance Planning**: plan period, upcoming projects, completed work
- **Member Information**: ownership transfers, fee history, apartment sizes

## CODE EXAMPLES

```python
# Schema usage with year-over-year data
from src.extraction.schema import IncomeStatement, NumberField, create_field_with_confidence

# Create income statement with current and previous year data
income_statement = IncomeStatement(
    revenue=NumberField(**create_field_with_confidence(4500000, 0.9, "source")),
    expenses=NumberField(**create_field_with_confidence(3200000, 0.9, "source")),
    net_income=NumberField(**create_field_with_confidence(1300000, 0.9, "source")),
    previous_year_revenue=NumberField(**create_field_with_confidence(4200000, 0.8, "source")),
    previous_year_expenses=NumberField(**create_field_with_confidence(3100000, 0.8, "source")),
    previous_year_net_income=NumberField(**create_field_with_confidence(1100000, 0.8, "source"))
)

# Calculate year-over-year change
current = income_statement.revenue.value
previous = income_statement.previous_year_revenue.value
if current and previous and previous > 0:
    change_percent = ((current - previous) / previous) * 100
    print(f"Revenue change: {change_percent:.1f}%")
```

## POST-COMPACTION VERIFICATION

1. **Test the schema implementation:**
   ```bash
   python test_schema_fields.py
   ```

2. **Run extraction with unverified fields detection:**
   ```bash
   export ZELDALINK_TEST_MODE=true
   ./run_sailor_extraction.sh
   ```

3. **Check schema improvement suggestions for unverified fields:**
   ```python
   import json
   with open('sailor_extraction_results.json', 'r') as f:
       results = json.load(f)
   for suggestion in results.get('schema_improvements', []):
       print(f"{suggestion['field_path']}.{suggestion['suggested_name']}: {suggestion['example_value']}")
   ```

## NEXT STEPS

1. **Test extraction with year-over-year fields**
   - Use test documents to verify correct extraction
   - Compare results across different LLM models

2. **Review unverified fields detection**
   - Analyze suggestions from extraction process
   - Add high-confidence fields to the schema

3. **Implement cross-page integration**
   - Focus on complex tables spanning multiple pages
   - Integrate financial data across sections

## FIELD VALIDATION PROCESS

Follow this three-step process for schema extension:
1. **Detection**: Identify potential fields in documents
2. **Validation**: Verify fields appear consistently with good confidence
3. **Integration**: Add validated fields to the schema

## PRE-COMPACTION PROCESS

Pre-compaction involves preparing the project for context compression by ensuring all documentation is clear, code is verified, and files are properly organized.

### 1. Documentation Review
- [ ] Verify START.md (this file) is complete and clear
- [ ] Check CRITICAL_INSTRUCTIONS.md points to the right files
- [ ] Ensure docs/STATE_SNAPSHOT.md accurately reflects current status
- [ ] Confirm next steps are clearly defined and prioritized

### 2. Code Verification
- [ ] Run schema verification test:
  ```bash
  python test_schema_fields.py
  ```
- [ ] Verify core functionality works in test mode:
  ```bash
  export ZELDALINK_TEST_MODE=true
  ./run_sailor_extraction.sh
  ```
- [ ] Check that unverified fields detection is working:
  ```bash
  python -c "from unverified_fields_guide import generate_prompt_section; print(generate_prompt_section())"
  ```

### 3. Decluttering and Git Management
- [ ] Declutter the repository according to our file structure:
  ```bash
  # Create organizational directories if they don't exist
  mkdir -p src/extraction
  mkdir -p docs
  mkdir -p backups
  mkdir -p test_results
  mkdir -p benchmarks
  
  # Move any loose Python files to appropriate locations
  find . -maxdepth 1 -name "*.py" | grep -v "test_schema_fields.py" | grep -v "unverified_fields_guide.py" | xargs -I{} mv {} src/
  
  # Organize documentation files
  find . -maxdepth 1 -name "*.md" | grep -v "START.md" | grep -v "CRITICAL_INSTRUCTIONS.md" | grep -v "README.md" | xargs -I{} mv {} docs/
  
  # Move old results to appropriate directories
  find . -maxdepth 1 -name "*_results.json" -exec mv {} test_results/ \;
  
  # Clean up temporary files
  find . -name "*.pyc" -delete
  find . -name "__pycache__" -type d -exec rm -rf {} +
  find . -name ".DS_Store" -delete
  find . -name "*.log" -exec mv {} logs/ \;
  
  # Create logs directory if moving log files
  mkdir -p logs
  ```
- [ ] Commit the decluttered repository:
  ```bash
  git add .
  git commit -m "Pre-compaction: Declutter repository and organize files"
  ```
- [ ] Create a complete backup:
  ```bash
  mkdir -p backups/pre_compaction_$(date +%Y%m%d)
  cp -r src/ backups/pre_compaction_$(date +%Y%m%d)/
  cp START.md CRITICAL_INSTRUCTIONS.md docs/STATE_SNAPSHOT.md backups/pre_compaction_$(date +%Y%m%d)/
  cp test_schema_fields.py unverified_fields_guide.py backups/pre_compaction_$(date +%Y%m%d)/
  ```

### 4. Final Confirmation Checklist
- [ ] Instructions are clear and comprehensive
- [ ] Current project status is accurately documented
- [ ] Next steps are explicitly defined and prioritized
- [ ] Core functionality is verified working
- [ ] All critical files are backed up
- [ ] Recovery path is clearly defined

### 5. Post-Compaction Recovery
After compaction, reestablish context with:
```
read START.md
```

## RECOVERY PROCEDURE

If context is lost during compaction:
1. Read this document (START.md) completely
2. Run `python test_schema_fields.py` to verify schema
3. Check the latest STATE_SNAPSHOT.md for detailed status