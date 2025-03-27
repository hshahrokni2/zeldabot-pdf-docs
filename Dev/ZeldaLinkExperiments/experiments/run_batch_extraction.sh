#!/bin/bash
# Run batch extraction on all OCR files
# This script processes all OCR JSON files in the mistral_ocr_results directory

# Set working directory
cd "$(dirname "$0")"

# Define directories
OCR_DIR="mistral_ocr_results"
OUTPUT_DIR="extracted_data"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Find all OCR JSON files
OCR_FILES=$(find "$OCR_DIR" -name "*_ocr.json" -not -path "*/batches/*")

# Check if any files were found
if [ -z "$OCR_FILES" ]; then
    echo "Error: No OCR JSON files found in $OCR_DIR"
    exit 1
fi

echo "Found $(echo "$OCR_FILES" | wc -l | xargs) OCR JSON files to process"

# Process each file
SUCCESS_COUNT=0
FAILURE_COUNT=0

for OCR_FILE in $OCR_FILES; do
    echo "===================================================="
    echo "Processing: $OCR_FILE"
    
    # Run extraction processor
    ./run_mistral_extraction.sh "$OCR_FILE" "$OUTPUT_DIR"
    
    # Check exit status
    if [ $? -eq 0 ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi
    
    echo "===================================================="
done

# Print summary
echo ""
echo "Batch Extraction Summary:"
echo "  Total files: $((SUCCESS_COUNT + FAILURE_COUNT))"
echo "  Successfully processed: $SUCCESS_COUNT"
echo "  Failed: $FAILURE_COUNT"

# List extracted files
echo ""
echo "Extracted files in $OUTPUT_DIR:"
ls -la "$OUTPUT_DIR"

# Return success if all files were processed successfully
if [ $FAILURE_COUNT -eq 0 ]; then
    exit 0
else
    exit 1
fi