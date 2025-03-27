# Message to Future Claude: LLM-Enhanced OCR Extraction Project

## Project Context

This project aims to enhance the ZeldaLink extraction system, which extracts structured data from Swedish Housing Association (BRF) reports. The current system uses regex pattern matching on OCR text, achieving only 38.46% accuracy compared to a baseline of 53.39%. Our goal is to implement a more accurate extraction approach using LLM processing of OCR text.

## Key Challenges Addressed

1. **OCR Quality Issues**: Mistral OCR API integration has been challenging due to format changes and rate limiting. We've implemented a PDF-to-images approach that splits PDFs into page images before OCR processing.

2. **Extraction Accuracy**: The regex approach struggles with context understanding and document variations. We've developed an LLM-based extraction that shows significantly better field coverage (~80% accuracy in tests).

3. **Technical Details**: We've navigated API format changes, Swedish text normalization, and hybrid extraction strategies.

## Current Implementation Status

1. **OCR Processing**: 
   - `updated_mistral_ocr.py`: Latest implementation that follows current Mistral OCR API format
   - Converts PDFs to images and processes in batches (3 pages per batch)
   - Handles rate limiting and combines results

2. **LLM Extraction**:
   - `local_ocr_llm_extraction.py`: Extracts text from PDF and sends to Mistral LLM
   - `direct_mistral_llm_extraction.py`: Processes OCR results with Mistral LLM
   - Extraction prompt has been refined for Swedish BRF reports

3. **Benchmark Comparison**:
   - `compare_extractions.py`: Compares LLM extraction with regex extraction
   - LLM shows better field coverage (22 vs 19 fields in tests)
   - LLM provides detailed confidence scores for each field

## Extraction Prompt Engineering

The most critical element of this system is the extraction prompt. The current version achieves ~80% accuracy and includes:

```
Analyse this Swedish housing association (BRF) annual report and extract structured data.

OCR TEXT:
{ocr_text}

Extract the following data in JSON format:

1. property_info:
   - designation: Property designation/Fastighetsbeteckning
   - organization_number: Organization number/Organisationsnummer
   - address: Address of the property/Adress
   - total_area: Total area in square meters/Total yta i kvadratmeter
   - residential_area: Residential area in square meters/Bostadsyta (BOA)
   - commercial_area: Commercial area in square meters/Lokalyta (LOA)
   - apartment_count: Number of apartments/Antal lägenheter
   - year_built: Year the property was built/Byggnadsår

2. financial_info:
   - total_revenue: Total revenue for the reporting year/Totala intäkter
   - total_expenses: Total expenses for the reporting year/Totala kostnader
   - profit_loss: Profit or loss for the year/Årets resultat
   - month_fee: Monthly fee per square meter/Månadsavgift per kvm

3. costs:
   - heating: Heating costs/Värmekostnader
   - electricity: Electricity costs/Elkostnader
   - water: Water and sewage costs/Vatten och avlopp
   - maintenance: Maintenance costs/Underhållskostnader
   - property_tax: Property tax/Fastighetsskatt
   - insurance: Insurance costs/Försäkringskostnader
   - administration: Administrative costs/Administrationskostnader

4. loans:
   - A list of loans with the following information for each:
     - lender: Name of the lender/Långivare
     - amount: Loan amount/Lånebelopp
     - interest_rate: Interest rate/Räntesats
     - term: Loan term or next refinancing date/Löptid eller omsättningsdatum

5. governance:
   - board_members: List of board members with their roles/Styrelsemedlemmar med roller
   - management_company: Management company, if any/Förvaltningsbolag, om det finns

IMPORTANT RULES:
1. Format all monetary values as numbers without currency symbols or spaces
2. Convert Swedish number format (e.g., "1 234,56") to standard format (1234.56)
3. Answer in the exact JSON format requested, with all values as the appropriate type
4. If you can't find a specific value, set it to null (not empty string or 0)
5. Include the confidence level for each field based on how certain you are
```

## Integration Path

To integrate this approach into the main pipeline:

1. **Hybrid Approach Implementation**:
   ```python
   def extract_data(pdf_path, use_llm=True, fallback_to_regex=True):
       # Extract OCR text
       ocr_text = extract_ocr_text(pdf_path)
       
       # Try LLM extraction first if enabled
       llm_result = None
       if use_llm:
           llm_result = extract_with_llm(ocr_text)
       
       # Fall back to regex if needed
       regex_result = None
       if llm_result is None or fallback_to_regex:
           regex_result = extract_with_regex(ocr_text)
       
       # Merge results or use best one
       if llm_result and regex_result:
           return merge_results(llm_result, regex_result)
       return llm_result or regex_result
   ```

2. **Confidence-Based Field Selection**:
   - Use confidence scores from LLM extraction to select most reliable fields
   - Fall back to regex for fields with low LLM confidence
   - Implement validation rules for consistency checking

## Test Results

Initial testing with synthetic data shows:

| Metric | Regex Approach | LLM Approach | Improvement |
|--------|---------------|--------------|-------------|
| Field Coverage | 19 fields | 22 fields | +3 fields |
| Extraction Accuracy | 38.46% | ~80%+ | +40%+ |
| Confidence Score | ~0.75 avg | ~0.92 avg | +0.17 |

Real-world testing is ongoing with the updated Mistral OCR API.

## Mistral API Notes

Recent changes to the Mistral OCR API require this format for image processing:

```python
{
    "model": "mistral-ocr-latest",
    "document": {
        "type": "image_url",
        "image_url": f"data:image/png;base64,{base64_image}"
    }
}
```

The endpoint is: `https://api.mistral.ai/v1/ocr/process`

## Next Steps for Future Claude

1. **Complete OCR Integration**: Finish the updated Mistral OCR implementation and test with real documents.

2. **Refine LLM Extraction**: Adjust prompts based on real OCR output quality and error analysis.

3. **Implement Hybrid Approach**: Build the confidence-based field selection system.

4. **Integrate with Main Pipeline**: Update `integrated_extraction.py` to use the hybrid approach.

5. **Benchmark with Real Data**: Run comprehensive benchmarks on all test documents.

6. **Documentation**: Update MISTRAL_OCR_IMPLEMENTATION.md with final implementation details.

## Critical Path Issues

1. **API Rate Limiting**: Handle Mistral API rate limits by implementing proper batching and retry logic.

2. **Swedish Text Normalization**: Ensure proper handling of Swedish characters and number formats.

3. **Balance Accuracy vs. Coverage**: Optimize the hybrid approach to maximize both field coverage and accuracy.

## Final Recommendations

The LLM-enhanced extraction shows significant promise for improving the ZeldaLink system, with potential to increase accuracy from 38.46% to 80%+. The hybrid approach provides robustness by combining the strengths of both methods.

Remember to always validate the extraction results against ground truth data and continuously refine the prompts based on real-world performance.

Good luck with the implementation!