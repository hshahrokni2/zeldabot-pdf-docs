#!/usr/bin/env python3
"""
Schema Improvement Analyzer and Consolidator.

This script analyzes schema improvement suggestions from multiple extraction runs,
consolidates common suggestions, and provides recommendations for schema updates.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
from datetime import datetime


class SchemaImprover:
    """
    Analyzes schema improvement suggestions and recommends schema updates.
    """
    
    def __init__(self, suggestions_dir: str = None, output_file: str = None):
        """
        Initialize the schema improver.
        
        Args:
            suggestions_dir: Directory containing schema improvement suggestion files
            output_file: Path to save the consolidated analysis
        """
        self.suggestions_dir = suggestions_dir
        self.output_file = output_file or "consolidated_schema_improvements.json"
        
        # Store suggestions by field path
        self.all_suggestions = []
        self.suggestions_by_path = defaultdict(list)
        
        # Track document sources
        self.document_sources = set()
    
    def load_suggestions(self, files: List[str] = None) -> int:
        """
        Load schema improvement suggestions from JSON files.
        
        Args:
            files: List of JSON files containing schema improvement suggestions
            
        Returns:
            Number of suggestions loaded
        """
        if files is None:
            # Find all schema improvement files in the directory
            if self.suggestions_dir:
                files = list(Path(self.suggestions_dir).glob("*schema_improvements*.json"))
            else:
                files = []
        
        total_loaded = 0
        
        for file_path in files:
            file_path = str(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract document source from filename
                doc_source = os.path.basename(file_path).split('_')[0]
                self.document_sources.add(doc_source)
                
                # Get suggestions
                suggestions = []
                if "suggestions" in data:
                    suggestions = data["suggestions"]
                elif "schema_improvements" in data and "suggestions" in data["schema_improvements"]:
                    suggestions = data["schema_improvements"]["suggestions"]
                
                # Add source information to each suggestion
                for suggestion in suggestions:
                    suggestion["source_file"] = file_path
                    suggestion["document_id"] = doc_source
                    
                    # Add to our collections
                    self.all_suggestions.append(suggestion)
                    self.suggestions_by_path[suggestion["field_path"]].append(suggestion)
                
                total_loaded += len(suggestions)
                print(f"Loaded {len(suggestions)} suggestions from {file_path}")
                
            except Exception as e:
                print(f"Error loading suggestions from {file_path}: {e}")
        
        return total_loaded
    
    def analyze_suggestions(self) -> Dict[str, Any]:
        """
        Analyze loaded schema improvement suggestions.
        
        Returns:
            Dictionary containing analysis results
        """
        if not self.all_suggestions:
            return {
                "error": "No suggestions loaded",
                "timestamp": datetime.now().isoformat()
            }
        
        # Get unique paths
        unique_paths = set(self.suggestions_by_path.keys())
        print(f"Found {len(unique_paths)} unique field paths across {len(self.all_suggestions)} total suggestions")
        
        # Analyze frequency of each suggestion path
        path_frequency = {}
        for path, suggestions in self.suggestions_by_path.items():
            path_frequency[path] = len(suggestions)
        
        # Sort paths by frequency
        sorted_paths = sorted(path_frequency.items(), key=lambda x: x[1], reverse=True)
        
        # Find common suggestions across documents
        common_suggestions = []
        document_count = len(self.document_sources)
        
        for path, frequency in sorted_paths:
            # Get all suggestions for this path
            path_suggestions = self.suggestions_by_path[path]
            
            # Count unique documents for this path
            doc_sources = set(s["document_id"] for s in path_suggestions)
            
            # Calculate average confidence
            avg_confidence = sum(s["confidence"] for s in path_suggestions) / len(path_suggestions)
            
            # Get most common suggested name and type
            name_counts = defaultdict(int)
            type_counts = defaultdict(int)
            example_values = []
            reasons = set()
            
            for s in path_suggestions:
                name_counts[s["suggested_name"]] += 1
                type_counts[s["suggested_type"]] += 1
                if "example_value" in s and s["example_value"] is not None:
                    example_values.append(s["example_value"])
                if "reason" in s and s["reason"]:
                    reasons.add(s["reason"])
            
            # Get most common name and type
            most_common_name = max(name_counts.items(), key=lambda x: x[1])[0]
            most_common_type = max(type_counts.items(), key=lambda x: x[1])[0]
            
            # Create consolidated suggestion
            consolidated = {
                "field_path": path,
                "suggested_name": most_common_name,
                "suggested_type": most_common_type,
                "confidence": avg_confidence,
                "frequency": frequency,
                "document_coverage": len(doc_sources) / document_count,
                "documents": list(doc_sources),
                "reasons": list(reasons),
                "example_values": example_values[:5]  # Limit to 5 examples
            }
            
            common_suggestions.append(consolidated)
        
        # Sort by document coverage and then by confidence
        common_suggestions.sort(key=lambda x: (x["document_coverage"], x["confidence"]), reverse=True)
        
        # Create recommendations
        recommendations = []
        for suggestion in common_suggestions:
            # Only recommend fields with high confidence or coverage
            if suggestion["confidence"] > 0.7 or suggestion["document_coverage"] > 0.5:
                path_parts = suggestion["field_path"].split(".")
                
                # Generate Pydantic model field code
                if suggestion["suggested_type"] == "string":
                    field_type = "Optional[StringField]"
                elif suggestion["suggested_type"] == "number":
                    field_type = "Optional[NumberField]"
                elif suggestion["suggested_type"] == "integer":
                    field_type = "Optional[IntegerField]"
                elif suggestion["suggested_type"] == "boolean":
                    field_type = "Optional[BooleanField]"
                elif suggestion["suggested_type"] == "array":
                    field_type = "List[Any]"
                elif suggestion["suggested_type"] == "object":
                    field_type = "Optional[Dict[str, Any]]"
                else:
                    field_type = f"Optional[{suggestion['suggested_type']}Field]"
                
                example_value = None
                if suggestion["example_values"]:
                    example_value = suggestion["example_values"][0]
                
                recommendations.append({
                    "field_path": suggestion["field_path"],
                    "field_name": suggestion["suggested_name"],
                    "field_type": field_type,
                    "confidence": suggestion["confidence"],
                    "coverage": suggestion["document_coverage"],
                    "example_value": example_value,
                    "pydantic_field": f"{suggestion['suggested_name']}: {field_type} = None"
                })
        
        return {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "total_suggestions": len(self.all_suggestions),
                "unique_paths": len(unique_paths),
                "document_sources": list(self.document_sources),
                "document_count": document_count
            },
            "consolidated_suggestions": common_suggestions,
            "recommendations": recommendations
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
            
            print(f"Saved analysis results to {self.output_file}")
            return self.output_file
        except Exception as e:
            print(f"Error saving analysis results: {e}")
            return ""
    
    def generate_implementation_code(self, analysis: Dict[str, Any]) -> str:
        """
        Generate Pydantic model implementation code for the recommendations.
        
        Args:
            analysis: Analysis results with recommendations
            
        Returns:
            Generated Pydantic model implementation code
        """
        if "recommendations" not in analysis or not analysis["recommendations"]:
            return "# No recommendations to implement"
        
        # Group recommendations by parent model
        model_fields = defaultdict(list)
        
        for rec in analysis["recommendations"]:
            path_parts = rec["field_path"].split(".")
            if len(path_parts) > 1:
                parent_model = path_parts[0]
                model_fields[parent_model].append(rec)
        
        code = "# Generated Pydantic model fields for schema improvements\n\n"
        code += "from typing import Dict, List, Any, Optional\n"
        code += "from src.extraction.schema import StringField, NumberField, IntegerField, BooleanField\n\n"
        
        for model, fields in model_fields.items():
            code += f"# Fields to add to the {model.capitalize()} model\n"
            
            for field in fields:
                if field.get("confidence", 0) > 0.7:
                    confidence_note = "HIGH CONFIDENCE"
                elif field.get("confidence", 0) > 0.5:
                    confidence_note = "MEDIUM CONFIDENCE"
                else:
                    confidence_note = "LOW CONFIDENCE"
                
                code += f"# {confidence_note} - Found in {int(field['coverage'] * 100)}% of documents\n"
                code += f"{field['pydantic_field']}  # Example value: {field['example_value']}\n\n"
        
        return code
    
    def process(self, files: List[str] = None) -> Dict[str, Any]:
        """
        Process schema improvement suggestions.
        
        Args:
            files: List of JSON files to process
            
        Returns:
            Analysis results
        """
        # Load suggestions
        count = self.load_suggestions(files)
        if count == 0:
            return {
                "error": "No suggestions loaded",
                "timestamp": datetime.now().isoformat()
            }
        
        # Analyze suggestions
        analysis = self.analyze_suggestions()
        
        # Save analysis
        self.save_analysis(analysis)
        
        # Generate implementation code
        implementation_code = self.generate_implementation_code(analysis)
        
        # Save implementation code
        impl_file = os.path.splitext(self.output_file)[0] + "_implementation.py"
        with open(impl_file, 'w', encoding='utf-8') as f:
            f.write(implementation_code)
        
        print(f"Saved implementation code to {impl_file}")
        
        return analysis


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze schema improvement suggestions")
    parser.add_argument("--dir", "-d", help="Directory containing schema improvement suggestion files")
    parser.add_argument("--files", "-f", nargs="+", help="Specific schema improvement suggestion files to analyze")
    parser.add_argument("--output", "-o", default="consolidated_schema_improvements.json", help="Output file path")
    
    args = parser.parse_args()
    
    improver = SchemaImprover(args.dir, args.output)
    
    analysis = improver.process(args.files)
    
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        return 1
    
    # Print summary
    print("\nSchema Improvement Analysis Summary:")
    print("=====================================")
    print(f"Total suggestions: {analysis['meta']['total_suggestions']}")
    print(f"Unique field paths: {analysis['meta']['unique_paths']}")
    print(f"Document sources: {', '.join(analysis['meta']['document_sources'])}")
    
    print("\nTop Recommendations:")
    for rec in analysis.get("recommendations", [])[:5]:
        print(f"- {rec['field_path']}: {rec['field_type']} (Confidence: {rec['confidence']:.2f}, "
              f"Coverage: {rec['coverage']*100:.0f}%)")
    
    print(f"\nFull analysis saved to {args.output}")
    print(f"Implementation code saved to {os.path.splitext(args.output)[0]}_implementation.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())