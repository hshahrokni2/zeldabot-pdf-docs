#!/bin/bash
# Run Mistral Extraction Processor
# This script runs the mistral_extraction_processor.py on OCR JSON output

# Set working directory
cd "$(dirname "$0")"

# Check if a file was provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_ocr_json> [output_path]"
    echo "Example: $0 mistral_ocr_results/282782_årsredovisning__brf_sailor.pdf_ocr.json extracted_data/"
    exit 1
fi

OCR_JSON_PATH="$1"
OUTPUT_DIR="${2:-extracted_data}"

# Check if the file exists
if [ ! -f "$OCR_JSON_PATH" ]; then
    echo "Error: OCR JSON file not found: $OCR_JSON_PATH"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Determine output filename
FILENAME=$(basename "$OCR_JSON_PATH" | sed 's/_ocr.json/_extracted.json/')
OUTPUT_PATH="$OUTPUT_DIR/$FILENAME"

# Find the Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Run the extraction processor
echo "Processing OCR data from: $OCR_JSON_PATH"
echo "Output will be saved to: $OUTPUT_PATH"

$PYTHON_CMD mistral_extraction_processor.py --ocr-json "$OCR_JSON_PATH" --output "$OUTPUT_PATH"

# Check exit status
STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo "Extraction completed successfully!"
    
    # Show a preview of the extracted data
    echo "Preview of extracted data:"
    $PYTHON_CMD -c "import json; f=open('$OUTPUT_PATH'); d=json.load(f); print(json.dumps({k:v for k,v in d.items() if k in ['organization', 'financial_report', 'meta']}, indent=2)[:500] + '...')"
    
    exit 0
else
    echo "Extraction failed with status code $STATUS"
    exit 1
fi