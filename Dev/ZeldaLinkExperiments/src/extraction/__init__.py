"""
Extraction module for Swedish housing association (BRF) annual reports.
"""

from src.extraction.schema import (
    BRFExtraction, ExtractionMeta, SchemaImprovement,
    Organization, PropertyDetails, FinancialReport,
    Board, FinancialMetrics, Loan, ExpensesDetail,
    StringField, NumberField, IntegerField, BooleanField,
    ConfidenceEnum, create_field_with_confidence
)

from src.extraction.extract import (
    extract_data, validate_extraction, save_extraction_results,
    MistralExtractor, GPT4Extractor, ClaudeExtractor
)

__all__ = [
    'BRFExtraction', 'ExtractionMeta', 'SchemaImprovement',
    'Organization', 'PropertyDetails', 'FinancialReport',
    'Board', 'FinancialMetrics', 'Loan', 'ExpensesDetail',
    'StringField', 'NumberField', 'IntegerField', 'BooleanField',
    'ConfidenceEnum', 'create_field_with_confidence',
    'extract_data', 'validate_extraction', 'save_extraction_results',
    'MistralExtractor', 'GPT4Extractor', 'ClaudeExtractor'
]