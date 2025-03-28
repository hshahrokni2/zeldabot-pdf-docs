#!/usr/bin/env python3
"""Fix income statement in mock data to include previous year fields."""

import os
import re
from pathlib import Path

def fix_income_statement(file_path):
    print(f"Reading file: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the _generate_mock_extraction method in the MistralExtractor class
    mistral_mock_pattern = r'def _generate_mock_extraction\(self\).*?return \{'
    mistral_mock = re.search(mistral_mock_pattern, content, re.DOTALL)
    
    if not mistral_mock:
        print("Couldn't find _generate_mock_extraction method")
        return False
    
    # Find where the income_statement is defined in the mock data
    income_stmt_pattern = r'"income_statement": \{\s*"revenue": \{"value": ([\d.]+).*?"expenses": \{"value": ([\d.]+).*?"net_income": \{"value": ([\d.]+)'
    income_stmt = re.search(income_stmt_pattern, content, re.DOTALL)
    
    if not income_stmt:
        print("Couldn't find income_statement in mock data")
        return False
    
    # Extract current values
    revenue = float(income_stmt.group(1))
    expenses = float(income_stmt.group(2))
    net_income = float(income_stmt.group(3))
    
    # Calculate previous year values (10% less)
    prev_revenue = revenue * 0.9
    prev_expenses = expenses * 0.9
    prev_net_income = net_income * 0.9
    
    # Find the end of the income_statement
    end_pattern = r'"income_statement": \{.*?\}\s*\}'
    end_match = re.search(end_pattern, content, re.DOTALL)
    
    if not end_match:
        print("Couldn't find the end of income_statement")
        return False
    
    # Prepare the replacement
    old_section = end_match.group(0)
    
    # Create new section with previous year data
    new_section = old_section[:-1] + ',\n'  # Remove the last } and add a comma
    new_section += '                    "previous_year_revenue": {"value": ' + str(prev_revenue) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                    "previous_year_expenses": {"value": ' + str(prev_expenses) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                    "previous_year_net_income": {"value": ' + str(prev_net_income) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                    "previous_year_revenue_breakdown": {\n'
    new_section += '                        "annual_fees": {"value": ' + str(revenue * 0.8) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                        "rental_income": {"value": ' + str(revenue * 0.15) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                        "other_income": {"value": ' + str(revenue * 0.05) + ', "confidence": 0.7, "source": "mock data"}\n'
    new_section += '                    },\n'
    new_section += '                    "previous_year_expense_breakdown": {\n'
    new_section += '                        "electricity": {"value": ' + str(expenses * 0.1) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                        "heating": {"value": ' + str(expenses * 0.2) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                        "water_and_sewage": {"value": ' + str(expenses * 0.1) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                        "property_maintenance": {"value": ' + str(expenses * 0.15) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                        "property_insurance": {"value": ' + str(expenses * 0.05) + ', "confidence": 0.7, "source": "mock data"},\n'
    new_section += '                        "financial_costs": {"value": ' + str(expenses * 0.4) + ', "confidence": 0.7, "source": "mock data"}\n'
    new_section += '                    }\n'
    new_section += '                }'
    
    # Replace the old section with the new one
    new_content = content.replace(old_section, new_section)
    
    # Write back to the file if there was a change
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print("Successfully added previous_year fields to income_statement")
        return True
    else:
        print("No changes were made")
        return False

if __name__ == "__main__":
    file_path = Path("/Users/hosseins/Dev/ZeldaLinkExperiments/src/extraction/extract.py")
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        exit(1)
    
    success = fix_income_statement(str(file_path))
    if success:
        print("Fixed income statement successfully!")
    else:
        print("Failed to fix income statement.")