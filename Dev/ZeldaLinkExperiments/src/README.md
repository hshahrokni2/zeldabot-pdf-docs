# Swedish BRF Document Extraction System

This directory contains the source code for the Swedish BRF document extraction system.

## Directory Structure

- `/extraction/` - Extraction logic and schema definitions
  - `schema.py` - Pydantic models for extraction schema
  - `extract.py` - Main extraction functions
  - `improve.py` - Schema improvement functions

- `/ocr/` - OCR processing functions
  - `processor.py` - OCR processing functions
  - `client.py` - Mistral OCR client

- `/validation/` - Validation functions
  - `validate.py` - Validation rules for extracted data
  - `confidence.py` - Confidence scoring functions

- `/tools/` - Utility functions and tools
  - `generate_schema_docs.py` - Generate schema documentation
  - `convert_schema.py` - Convert between schema versions

## Main Components

### Extraction Schema
The extraction schema is defined using Pydantic models in `extraction/schema.py`.
This provides strong typing, validation, and documentation.

### OCR Processing
OCR processing is handled by the Mistral OCR API, with client implementation
in `ocr/client.py`.

### Extraction Logic
The main extraction functions are in `extraction/extract.py`. This includes
the self-learning extraction loop and schema improvement suggestions.

### Validation
Validation functions in `validation/validate.py` provide additional checks
beyond basic Pydantic validation.

## Getting Started
See the main README.md in the project root for usage instructions.