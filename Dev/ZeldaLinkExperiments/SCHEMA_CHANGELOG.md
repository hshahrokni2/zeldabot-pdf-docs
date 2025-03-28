# Schema Changelog - Version 2.0

## Major Changes

The schema has been updated to version 2.0 with significant enhancements to support the extraction of Swedish BRF documents. This document outlines the key changes made to the schema.

## Structural Changes

1. **Confidence and Source Tracking**
   - Every field now follows a structured format with value, confidence, and source attributes
   - Example:
   ```json
   "organization_name": {
     "value": "BRF Sailor",
     "confidence": 0.95,
     "source": "page 1, paragraph 1"
   }
   ```

2. **Structured Address Components**
   - Added a new `address_components` object with structured fields:
     - street
     - number
     - postal_code
     - municipality
   - Original `address` field retained for backward compatibility

3. **Financial Metrics Section**
   - New top-level section for key financial ratios and metrics
   - Includes monthly_fee_per_sqm, debt_per_sqm, energy_consumption
   - Directly maps to data commonly found in Swedish BRF reports

4. **Enhanced Metadata**
   - Added extraction_method field to track source of data (regex, llm, hybrid)
   - Added ocr_source field to track source of OCR text
   - Added document_language field (defaulting to sv-SE)
   - Added normalization_rules to document Swedish number format handling

## Field Additions

1. **New Board Member Fields**
   - Enhanced auditor information with both name and company
   - Added confidence and source tracking to board members

2. **Source References**
   - All entities now include source tracking to document source page/section
   - Source information helps with validation and audit trails

3. **Financial Metrics**
   - Added monthly_fee_per_sqm (månadsavgift per kvm)
   - Added debt_per_sqm (skuld per kvm)
   - Added energy_consumption (kWh/sqm/year)
   - Added annual_fee_change_percent

## Special Format Handling

1. **Swedish Format Normalization**
   - New meta.normalization_rules section describes how Swedish formats are handled
   - Documents the conversion of "1 234,56 kr" to 1234.56
   - Default decimal separator set to "." and thousand separator to ""

## Confidence Implementation

All extractable fields now follow a consistent structure for confidence scoring:

```json
{
  "field_name": {
    "value": "extracted value",
    "confidence": 0.95,
    "source": "page reference"
  }
}
```

## Migration Notes

1. Applications using the previous schema will need to be updated to handle the new structure
2. The enhanced format allows more detailed extraction and validation
3. For backward compatibility, you can extract just the "value" key from each field

## Future Development

1. Consider adding field history tracking for corrections
2. Explore multilingual support beyond Swedish
3. Consider translation capabilities for exported data