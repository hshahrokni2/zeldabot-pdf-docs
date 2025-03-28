#!/usr/bin/env python3
"""Fix extraction templates to include new fields."""

import os
import re
from pathlib import Path

def fix_extraction_template(file_path):
    print(f"Reading file: {file_path}")
    # Create backup first
    backup_path = f"{file_path}.bak3"
    os.system(f"cp {file_path} {backup_path}")
    print(f"Created backup at: {backup_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Let's take a different approach - replace the entire extraction schema sections
    # Define the old patterns and new replacements for each extractor
    replacements = []
    
    # The problematic part is inside _create_extraction_prompt methods
    # Let's find each method and replace its content
    
    # Find all _create_extraction_prompt methods
    method_pattern = r'def _create_extraction_prompt\(self\).*?return f""".*?"""'
    methods = re.findall(method_pattern, content, re.DOTALL)
    
    if not methods:
        print("No extraction prompt methods found!")
        return False
    
    print(f"Found {len(methods)} extraction prompt methods.")
    
    # Carefully replace the methods
    for i, method in enumerate(methods):
        # Keep all the parts except the schema
        parts = method.split('EXTRACTION SCHEMA:')
        if len(parts) != 2:
            print(f"Warning: Method {i+1} doesn't have an extraction schema section!")
            continue
        
        header = parts[0]
        schema_and_rest = parts[1].split('IMPORTANT NOTES:')
        if len(schema_and_rest) != 2:
            print(f"Warning: Method {i+1} doesn't have the expected structure!")
            continue
        
        notes = schema_and_rest[1]
        
        # Create the new content with the updated schema
        new_method = header + 'EXTRACTION SCHEMA:\n'
        new_method += '        {\n'
        new_method += '          "organization": {\n'
        new_method += '            "organization_name": {"value": string, "confidence": float, "source": string},\n'
        new_method += '            "organization_number": {"value": string, "confidence": float, "source": string},\n'
        new_method += '            "registered_office": {"value": string, "confidence": float, "source": string},\n'
        new_method += '            "contact_details": {\n'
        new_method += '              "phone": {"value": string, "confidence": float, "source": string},\n'
        new_method += '              "email": {"value": string, "confidence": float, "source": string},\n'
        new_method += '              "website": {"value": string, "confidence": float, "source": string}\n'
        new_method += '            }\n'
        new_method += '          },\n'
        new_method += '          "property_details": {\n'
        new_method += '            "property_designation": {"value": string, "confidence": float, "source": string},\n'
        new_method += '            "address": {"value": string, "confidence": float, "source": string},\n'
        new_method += '            "total_area_sqm": {"value": number, "confidence": float, "source": string},\n'
        new_method += '            "residential_area_sqm": {"value": number, "confidence": float, "source": string},\n'
        new_method += '            "commercial_area_sqm": {"value": number, "confidence": float, "source": string},\n'
        new_method += '            "number_of_apartments": {"value": number, "confidence": float, "source": string},\n'
        new_method += '            "year_built": {"value": string, "confidence": float, "source": string}\n'
        new_method += '          },\n'
        new_method += '          "financial_report": {\n'
        new_method += '            "annual_report_year": {"value": string, "confidence": float, "source": string},\n'
        new_method += '            "balance_sheet": {\n'
        new_method += '              "assets": {\n'
        new_method += '                "total_assets": {"value": number, "confidence": float, "source": string}\n'
        new_method += '              },\n'
        new_method += '              "liabilities": {\n'
        new_method += '                "total_liabilities": {"value": number, "confidence": float, "source": string}\n'
        new_method += '              },\n'
        new_method += '              "equity": {"value": number, "confidence": float, "source": string}\n'
        new_method += '            },\n'
        new_method += '            "income_statement": {\n'
        new_method += '              "revenue": {"value": number, "confidence": float, "source": string},\n'
        new_method += '              "expenses": {"value": number, "confidence": float, "source": string},\n'
        new_method += '              "net_income": {"value": number, "confidence": float, "source": string},\n'
        new_method += '              "revenue_breakdown": {\n'
        new_method += '                "annual_fees": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "rental_income": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "other_income": {"value": number, "confidence": float, "source": string}\n'
        new_method += '              },\n'
        new_method += '              "expense_breakdown": {\n'
        new_method += '                "electricity": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "heating": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "water_and_sewage": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "waste_management": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "property_maintenance": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "repairs": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "maintenance": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "property_tax": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "property_insurance": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "cable_tv_internet": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "board_costs": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "management_fees": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "other_operating_costs": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "financial_costs": {"value": number, "confidence": float, "source": string}\n'
        new_method += '              },\n'
        new_method += '              "previous_year_revenue": {"value": number, "confidence": float, "source": string},\n'
        new_method += '              "previous_year_expenses": {"value": number, "confidence": float, "source": string},\n'
        new_method += '              "previous_year_net_income": {"value": number, "confidence": float, "source": string},\n'
        new_method += '              "previous_year_revenue_breakdown": {\n'
        new_method += '                "annual_fees": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "rental_income": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "other_income": {"value": number, "confidence": float, "source": string}\n'
        new_method += '              },\n'
        new_method += '              "previous_year_expense_breakdown": {\n'
        new_method += '                "electricity": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "heating": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "water_and_sewage": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "waste_management": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "property_maintenance": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "repairs": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "maintenance": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "property_tax": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "property_insurance": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "cable_tv_internet": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "board_costs": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "management_fees": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "other_operating_costs": {"value": number, "confidence": float, "source": string},\n'
        new_method += '                "financial_costs": {"value": number, "confidence": float, "source": string}\n'
        new_method += '              }\n'
        new_method += '            }\n'
        new_method += '          },\n'
        new_method += '          "financial_metrics": {\n'
        new_method += '            "monthly_fee_per_sqm": {"value": number, "confidence": float, "source": string},\n'
        new_method += '            "debt_per_sqm": {"value": number, "confidence": float, "source": string},\n'
        new_method += '            "loan_amortization_amount": {"value": number, "confidence": float, "source": string},\n'
        new_method += '            "total_debt": {"value": number, "confidence": float, "source": string},\n'
        new_method += '            "average_interest_rate": {"value": number, "confidence": float, "source": string}\n'
        new_method += '          },\n'
        new_method += '          "financial_loans": [\n'
        new_method += '            {\n'
        new_method += '              "lender": string,\n'
        new_method += '              "amount": number,\n'
        new_method += '              "interest_rate": number,\n'
        new_method += '              "maturity_date": string,\n'
        new_method += '              "confidence": float,\n'
        new_method += '              "source": string\n'
        new_method += '            }\n'
        new_method += '          ],\n'
        new_method += '          "board": {\n'
        new_method += '            "board_members": [\n'
        new_method += '              {\n'
        new_method += '                "name": string,\n'
        new_method += '                "role": string,\n'
        new_method += '                "confidence": float,\n'
        new_method += '                "source": string\n'
        new_method += '              }\n'
        new_method += '            ]\n'
        new_method += '          },\n'
        new_method += '          "schema_improvements": {\n'
        new_method += '            "suggestions": [\n'
        new_method += '              {\n'
        new_method += '                "field_path": string,  // Where in the schema this field should be added (e.g., "financial_metrics.loan_amortization_amount")\n'
        new_method += '                "suggested_name": string,  // The suggested field name\n'
        new_method += '                "suggested_type": string,  // The data type (string, number, boolean, array, object)\n'
        new_method += '                "example_value": any,     // An example value found in the document\n'
        new_method += '                "reason": string,         // Why this field should be added\n'
        new_method += '                "confidence": float       // Confidence in this suggestion (0.0-1.0)\n'
        new_method += '              }\n'
        new_method += '            ],\n'
        new_method += '            "model": string,\n'
        new_method += '            "timestamp": string\n'
        new_method += '          },\n'
        new_method += '          "meta": {\n'
        new_method += '            "extraction_confidence": float,\n'
        new_method += '            "extraction_date": string,\n'
        new_method += '            "extraction_method": string,\n'
        new_method += '            "ocr_source": string\n'
        new_method += '          }\n'
        new_method += '        }\n'
        new_method += '        IMPORTANT NOTES:' + notes
        
        # Replace the old method with the new one
        content = content.replace(method, new_method)
    
    print("Writing updated content to file...")
    with open(file_path, 'w') as f:
        f.write(content)
    
    return True

if __name__ == "__main__":
    file_path = Path("/Users/hosseins/Dev/ZeldaLinkExperiments/src/extraction/extract.py")
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        exit(1)
    
    success = fix_extraction_template(str(file_path))
    if success:
        print("Fixed extraction templates successfully!")
    else:
        print("Failed to fix extraction templates.")