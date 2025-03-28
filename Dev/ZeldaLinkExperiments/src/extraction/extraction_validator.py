#!/usr/bin/env python3
"""
Extraction Validator

This script validates extraction results by comparing them across different 
documents and models, calculating consistency scores, and identifying
potential extraction errors.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime

from src.extraction.schema import (
    BRFExtraction, validate_extraction
)


class ExtractionValidator:
    """
    Validates extraction results by comparing across documents and models.
    """
    
    def __init__(self, extraction_dir: str = None, output_file: str = None):
        """
        Initialize the extraction validator.
        
        Args:
            extraction_dir: Directory containing extraction result files
            output_file: Path to save the validation report
        """
        self.extraction_dir = extraction_dir
        self.output_file = output_file or "extraction_validation_report.json"
        
        # Store extractions by document and model
        self.extractions = {}
        self.documents = set()
        self.models = set()
        
        # Extraction metrics
        self.field_metrics = defaultdict(lambda: {
            "values": defaultdict(int),
            "documents": set(),
            "models": set(),
            "confidence_sum": 0,
            "confidence_count": 0,
            "missing_count": 0,
            "total_extractions": 0
        })
    
    def load_extractions(self, files: List[str] = None) -> int:
        """
        Load extraction results from JSON files.
        
        Args:
            files: List of JSON files containing extraction results
            
        Returns:
            Number of extractions loaded
        """
        if files is None:
            # Find all extraction result files in the directory
            if self.extraction_dir:
                # Find all JSON files except those containing "schema_improvements"
                files = [
                    f for f in Path(self.extraction_dir).glob("*.json")
                    if "schema_improvements" not in f.name
                ]
            else:
                files = []
        
        total_loaded = 0
        
        for file_path in files:
            file_path = str(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    extraction = json.load(f)
                
                # Extract document and model information from filename
                filename = os.path.basename(file_path)
                parts = filename.split('_')
                
                # Try to identify document ID
                doc_id = None
                for part in parts:
                    if part.startswith("282") or part.startswith("283"):
                        doc_id = part
                        break
                
                if doc_id is None:
                    # Fallback to first part of filename
                    doc_id = parts[0]
                
                # Try to identify model
                model = "unknown"
                if "mistral" in filename:
                    model = "mistral"
                elif "gpt" in filename:
                    model = "gpt"
                elif "claude" in filename:
                    model = "claude"
                
                # Store the extraction
                key = (doc_id, model)
                self.extractions[key] = extraction
                self.documents.add(doc_id)
                self.models.add(model)
                
                # Validate the extraction against Pydantic models
                is_valid, errors = validate_extraction(extraction)
                if not is_valid:
                    print(f"Warning: {file_path} has validation errors:")
                    for error in errors[:5]:  # Show only the first 5 errors
                        print(f"  - {error}")
                
                total_loaded += 1
                print(f"Loaded extraction from {file_path} (Document: {doc_id}, Model: {model})")
                
            except Exception as e:
                print(f"Error loading extraction from {file_path}: {e}")
        
        return total_loaded
    
    def _get_field_value(self, extraction: Dict[str, Any], field_path: str) -> Tuple[Any, float]:
        """
        Get a field value from an extraction by its path.
        
        Args:
            extraction: Extraction data
            field_path: Dot-notation path to the field
            
        Returns:
            Tuple of (field_value, confidence) or (None, 0.0) if not found
        """
        path_parts = field_path.split('.')
        current = extraction
        
        for part in path_parts[:-1]:
            if part not in current:
                return None, 0.0
            current = current[part]
            
            if current is None:
                return None, 0.0
        
        last_part = path_parts[-1]
        if last_part not in current:
            return None, 0.0
        
        field = current[last_part]
        
        # Handle different field formats
        if isinstance(field, dict) and "value" in field:
            # Field with confidence
            confidence = field.get("confidence", 0.0)
            return field["value"], confidence
        else:
            # Direct value
            return field, 0.0
    
    def analyze_extractions(self) -> Dict[str, Any]:
        """
        Analyze extraction results for consistency and identify potential errors.
        
        Returns:
            Dictionary containing validation results
        """
        if not self.extractions:
            return {
                "error": "No extractions loaded",
                "timestamp": datetime.now().isoformat()
            }
        
        # List of common fields to analyze
        common_fields = [
            "organization.organization_name",
            "organization.organization_number", 
            "property_details.property_designation",
            "property_details.total_area_sqm",
            "property_details.residential_area_sqm",
            "property_details.number_of_apartments",
            "property_details.year_built",
            "financial_report.annual_report_year",
            "financial_report.balance_sheet.assets.total_assets",
            "financial_report.balance_sheet.liabilities.total_liabilities",
            "financial_report.balance_sheet.equity",
            "financial_report.income_statement.revenue",
            "financial_report.income_statement.expenses",
            "financial_report.income_statement.net_income",
            "financial_metrics.monthly_fee_per_sqm",
            "financial_metrics.debt_per_sqm"
        ]
        
        # Track field values across extractions
        for (doc_id, model), extraction in self.extractions.items():
            for field_path in common_fields:
                value, confidence = self._get_field_value(extraction, field_path)
                
                # Update metrics for this field
                metrics = self.field_metrics[field_path]
                metrics["total_extractions"] += 1
                
                if value is not None:
                    # Convert value to string for comparison
                    str_value = str(value)
                    metrics["values"][str_value] += 1
                    metrics["documents"].add(doc_id)
                    metrics["models"].add(model)
                    metrics["confidence_sum"] += confidence
                    metrics["confidence_count"] += 1
                else:
                    metrics["missing_count"] += 1
        
        # Calculate consistency and confidence scores
        field_consistency = {}
        for field_path, metrics in self.field_metrics.items():
            if metrics["total_extractions"] == 0:
                continue
            
            # Get most common value and its frequency
            values = metrics["values"]
            if not values:
                consistency = 0.0
                most_common_value = None
                value_frequency = 0
            else:
                most_common_value, value_frequency = max(values.items(), key=lambda x: x[1])
                consistency = value_frequency / metrics["total_extractions"]
            
            # Calculate average confidence
            avg_confidence = 0.0
            if metrics["confidence_count"] > 0:
                avg_confidence = metrics["confidence_sum"] / metrics["confidence_count"]
            
            # Document and model coverage
            doc_coverage = len(metrics["documents"]) / len(self.documents)
            model_coverage = len(metrics["models"]) / len(self.models)
            
            field_consistency[field_path] = {
                "consistency": consistency,
                "confidence": avg_confidence,
                "document_coverage": doc_coverage,
                "model_coverage": model_coverage,
                "most_common_value": most_common_value,
                "value_frequency": value_frequency,
                "total_extractions": metrics["total_extractions"],
                "missing_count": metrics["missing_count"],
                "missing_rate": metrics["missing_count"] / metrics["total_extractions"]
            }
        
        # Sort fields by consistency
        sorted_consistency = sorted(
            field_consistency.items(),
            key=lambda x: x[1]["consistency"],
            reverse=True
        )
        
        # Identify potential errors
        potential_errors = []
        for field_path, metrics in sorted_consistency:
            # Low consistency but high coverage suggests extraction errors
            if metrics["consistency"] < 0.7 and metrics["document_coverage"] > 0.5:
                # Get all possible values
                values = self.field_metrics[field_path]["values"]
                
                potential_errors.append({
                    "field_path": field_path,
                    "consistency": metrics["consistency"],
                    "confidence": metrics["confidence"],
                    "most_common_value": metrics["most_common_value"],
                    "possible_values": [
                        {"value": value, "frequency": freq / metrics["total_extractions"]}
                        for value, freq in values.items()
                    ]
                })
        
        # Create document comparison
        document_comparison = {}
        for doc_id in self.documents:
            doc_values = {}
            for field_path in common_fields:
                field_values = []
                
                for model in self.models:
                    key = (doc_id, model)
                    if key in self.extractions:
                        value, confidence = self._get_field_value(self.extractions[key], field_path)
                        if value is not None:
                            field_values.append({
                                "model": model,
                                "value": value,
                                "confidence": confidence
                            })
                
                if field_values:
                    doc_values[field_path] = field_values
            
            document_comparison[doc_id] = doc_values
        
        return {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "total_extractions": len(self.extractions),
                "documents": list(self.documents),
                "models": list(self.models)
            },
            "field_consistency": dict(sorted_consistency),
            "potential_errors": potential_errors,
            "document_comparison": document_comparison
        }
    
    def save_analysis(self, analysis: Dict[str, Any]) -> str:
        """
        Save analysis results to a JSON file.
        
        Args:
            analysis: Analysis results to save
            
        Returns:
            Path to the saved file
        """
        try:
            # Ensure directory exists
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            
            print(f"Saved validation results to {self.output_file}")
            return self.output_file
        except Exception as e:
            print(f"Error saving validation results: {e}")
            return ""
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a human-readable validation report in Markdown format.
        
        Args:
            analysis: Analysis results
            
        Returns:
            Markdown report content
        """
        if "error" in analysis:
            return f"# Extraction Validation Error\n\n{analysis['error']}"
        
        report = "# Extraction Validation Report\n\n"
        report += f"Generated: {analysis['meta']['timestamp']}\n\n"
        
        report += "## Overview\n\n"
        report += f"- Total extractions analyzed: {analysis['meta']['total_extractions']}\n"
        report += f"- Documents analyzed: {', '.join(analysis['meta']['documents'])}\n"
        report += f"- Models compared: {', '.join(analysis['meta']['models'])}\n\n"
        
        report += "## Field Consistency\n\n"
        report += "| Field | Consistency | Confidence | Common Value | Missing % |\n"
        report += "| ----- | ----------- | ---------- | ------------ | -------- |\n"
        
        for field_path, metrics in analysis["field_consistency"].items():
            most_common = str(metrics["most_common_value"])
            if len(most_common) > 30:
                most_common = most_common[:27] + "..."
            
            report += f"| {field_path} | {metrics['consistency']:.2f} | {metrics['confidence']:.2f} | {most_common} | {metrics['missing_rate']:.2f} |\n"
        
        report += "\n## Potential Extraction Errors\n\n"
        
        if analysis["potential_errors"]:
            for error in analysis["potential_errors"]:
                report += f"### {error['field_path']}\n\n"
                report += f"- Consistency: {error['consistency']:.2f}\n"
                report += f"- Confidence: {error['confidence']:.2f}\n"
                report += "- Possible values:\n"
                
                for val in error["possible_values"]:
                    report += f"  - {val['value']} (frequency: {val['frequency']:.2f})\n"
                
                report += "\n"
        else:
            report += "No potential errors identified with the current criteria.\n\n"
        
        report += "## Document Comparison\n\n"
        
        for doc_id, fields in analysis["document_comparison"].items():
            report += f"### {doc_id}\n\n"
            
            for field_path, values in fields.items():
                report += f"#### {field_path}\n\n"
                
                for val in values:
                    report += f"- {val['model']}: {val['value']} (confidence: {val['confidence']:.2f})\n"
                
                report += "\n"
        
        return report
    
    def process(self, files: List[str] = None) -> Dict[str, Any]:
        """
        Process extraction results for validation.
        
        Args:
            files: List of JSON files to process
            
        Returns:
            Validation results
        """
        # Load extractions
        count = self.load_extractions(files)
        if count == 0:
            return {
                "error": "No extractions loaded",
                "timestamp": datetime.now().isoformat()
            }
        
        # Analyze extractions
        analysis = self.analyze_extractions()
        
        # Save analysis
        self.save_analysis(analysis)
        
        # Generate report
        report = self.generate_report(analysis)
        
        # Save report
        report_file = os.path.splitext(self.output_file)[0] + "_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Saved validation report to {report_file}")
        
        return analysis


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Validate extraction results")
    parser.add_argument("--dir", "-d", help="Directory containing extraction result files")
    parser.add_argument("--files", "-f", nargs="+", help="Specific extraction files to analyze")
    parser.add_argument("--output", "-o", default="extraction_validation.json", help="Output file path")
    
    args = parser.parse_args()
    
    validator = ExtractionValidator(args.dir, args.output)
    
    analysis = validator.process(args.files)
    
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        return 1
    
    # Print summary
    print("\nExtraction Validation Summary:")
    print("==============================")
    print(f"Total extractions: {analysis['meta']['total_extractions']}")
    print(f"Documents analyzed: {', '.join(analysis['meta']['documents'])}")
    print(f"Models compared: {', '.join(analysis['meta']['models'])}")
    
    print("\nTop Consistency Fields:")
    for i, (field, metrics) in enumerate(list(analysis["field_consistency"].items())[:5]):
        print(f"- {field}: {metrics['consistency']:.2f} consistency, {metrics['confidence']:.2f} confidence")
    
    print("\nPotential Errors:")
    if analysis["potential_errors"]:
        for error in analysis["potential_errors"][:3]:  # Show top 3
            print(f"- {error['field_path']}: {error['consistency']:.2f} consistency")
    else:
        print("No potential errors identified with the current criteria.")
    
    report_file = os.path.splitext(args.output)[0] + "_report.md"
    print(f"\nFull validation results saved to {args.output}")
    print(f"Validation report saved to {report_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())