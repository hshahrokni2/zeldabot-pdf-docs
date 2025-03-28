#!/usr/bin/env python3
"""
Test script for self-learning extraction with schema improvements.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from src.extraction import (
    extract_data, validate_extraction, save_extraction_results
)


def read_ocr_data(file_path):
    """
    Read OCR data from a file.
    
    Args:
        file_path: Path to the OCR JSON file
        
    Returns:
        OCR text content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to load as JSON first
            try:
                data = json.load(f)
                # If this is a Mistral OCR format with pages
                if 'pages' in data:
                    # Concatenate all page text
                    full_text = ""
                    for page in data['pages']:
                        if 'markdown' in page:
                            full_text += page['markdown'] + "\n\n"
                        elif 'text' in page:
                            full_text += page['text'] + "\n\n"
                    return full_text
                else:
                    # Just return the raw JSON string
                    return json.dumps(data, ensure_ascii=False)
            except json.JSONDecodeError:
                # Not JSON, read as regular text
                f.seek(0)  # Reset file pointer
                return f.read()
    except Exception as e:
        print(f"Error reading OCR data: {e}")
        return None


def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description="Test extraction with schema improvements")
    parser.add_argument("--ocr", "-i", required=True, help="Path to OCR data file")
    parser.add_argument("--output", "-o", default="extraction_results", help="Output directory")
    parser.add_argument("--model", "-m", default="mistral-large-latest", 
                      help="Model to use (mistral-large-latest, gpt-4-0125-preview, claude-3-sonnet-20240229)")
    parser.add_argument("--test-mode", "-t", action="store_true", help="Run in test mode with mock data")
    
    args = parser.parse_args()
    
    # Set test mode environment variable if requested
    if args.test_mode:
        os.environ["ZELDALINK_TEST_MODE"] = "true"
        print("Running in test mode with mock data")
    
    # Read OCR data
    ocr_text = read_ocr_data(args.ocr)
    if not ocr_text:
        print(f"Error: Could not read OCR data from {args.ocr}")
        return 1
    
    # Get filename without extension
    file_base = Path(args.ocr).stem
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract data
    print(f"Extracting data from {args.ocr} using {args.model}...")
    results = extract_data(ocr_text, model=args.model)
    
    # Check for errors
    if "error" in results:
        print(f"Error during extraction: {results['error']}")
        return 1
    
    # Validate extraction
    print("Validating extraction results...")
    is_valid, error_messages = validate_extraction(results["extraction"])
    
    if not is_valid:
        print("Validation errors:")
        for error in error_messages:
            print(f"  - {error}")
    else:
        print("Extraction results are valid!")
    
    # Save extraction results
    output_path = os.path.join(args.output, f"{file_base}_{args.model.split('-')[0]}_{timestamp}.json")
    if save_extraction_results(results["extraction"], output_path):
        print(f"Saved extraction results to {output_path}")
    
    # Save schema improvement suggestions separately
    if results.get("schema_improvements"):
        schema_output = os.path.join(args.output, f"{file_base}_schema_improvements_{timestamp}.json")
        with open(schema_output, 'w', encoding='utf-8') as f:
            schema_data = {
                "suggestions": results["schema_improvements"],
                "model": args.model,
                "timestamp": timestamp,
                "source_file": args.ocr
            }
            json.dump(schema_data, f, ensure_ascii=False, indent=2)
        print(f"Saved schema improvement suggestions to {schema_output}")
    
    # Print summary
    print("\nExtraction Summary:")
    print("===================")
    extraction = results["extraction"]
    
    print(f"Organization: {extraction.get('organization', {}).get('organization_name', {}).get('value', 'Not found')}")
    print(f"Org Number: {extraction.get('organization', {}).get('organization_number', {}).get('value', 'Not found')}")
    print(f"Report Year: {extraction.get('financial_report', {}).get('annual_report_year', {}).get('value', 'Not found')}")
    
    loans = extraction.get('financial_loans', [])
    print(f"Loans: {len(loans)} found")
    
    board_members = extraction.get('board', {}).get('board_members', [])
    print(f"Board Members: {len(board_members)} found")
    
    schema_improvements = results.get("schema_improvements", [])
    print(f"Schema Improvements: {len(schema_improvements)} suggestions")
    
    tokens = results.get("tokens_used", 0)
    print(f"Tokens Used: {tokens}")
    
    print("\nSchema Improvement Suggestions:")
    print("===============================")
    for i, suggestion in enumerate(schema_improvements[:5], 1):  # Show at most 5
        print(f"{i}. {suggestion['field_path']}: {suggestion['suggested_name']} ({suggestion['suggested_type']})")
        print(f"   Reason: {suggestion['reason']}")
        print(f"   Example: {suggestion['example_value']}")
        print()
    
    if len(schema_improvements) > 5:
        print(f"... and {len(schema_improvements) - 5} more suggestions")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())