#!/usr/bin/env python3
"""Fix extraction templates to include new fields."""

import os
import re
from pathlib import Path

def fix_extraction_template(file_path):
    print(f"Reading file: {file_path}")
    # Create backup first
    backup_path = f"{file_path}.bak4"
    os.system(f"cp {file_path} {backup_path}")
    print(f"Created backup at: {backup_path}")
    
    with open(backup_path, 'r') as f:
        content = f.read()
    
    # Let's simplify by restoring the original file, then making simpler changes
    with open(file_path, 'w') as f:
        f.write(content)
    
    # Now let's modify the test mock extraction data to include our new fields
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add previous_year fields to mock data for MistralExtractor
    # Find the mock_extraction function
    mistral_mock_pattern = r'def _generate_mock_extraction\(self\).*?return \{'
    mistral_mock = re.search(mistral_mock_pattern, content, re.DOTALL)
    
    if mistral_mock:
        print("Found MistralExtractor mock data")
        # Find the income_statement section
        income_stmt_pattern = r'"income_statement": \{[^}]*\}'
        income_stmt = re.search(income_stmt_pattern, content, re.DOTALL)
        
        if income_stmt:
            print("Found income_statement section")
            old_section = income_stmt.group(0)
            
            # Extract existing values
            revenue_match = re.search(r'"revenue": \{"value": (\d+\.\d+)', old_section)
            expenses_match = re.search(r'"expenses": \{"value": (\d+\.\d+)', old_section)
            net_income_match = re.search(r'"net_income": \{"value": (\d+\.\d+)', old_section)
            
            if revenue_match and expenses_match and net_income_match:
                # Calculate previous year values (10% less)
                prev_revenue = float(revenue_match.group(1)) * 0.9
                prev_expenses = float(expenses_match.group(1)) * 0.9
                prev_net_income = float(net_income_match.group(1)) * 0.9
                
                # Create new section with previous year values
                new_section = old_section.rstrip('}') + ',\n'
                new_section += f'                    "previous_year_revenue": {{"value": {prev_revenue}, "confidence": 0.7, "source": "mock data"}},\n'
                new_section += f'                    "previous_year_expenses": {{"value": {prev_expenses}, "confidence": 0.7, "source": "mock data"}},\n'
                new_section += f'                    "previous_year_net_income": {{"value": {prev_net_income}, "confidence": 0.7, "source": "mock data"}}\n'
                new_section += '                }'
                
                # Replace the old section with the new one
                content = content.replace(old_section, new_section)
                print("Added previous_year fields to income_statement")
            else:
                print("Couldn't find required values in income_statement")
        
        # Add average_interest_rate to financial_metrics
        metrics_pattern = r'"financial_metrics": \{[^}]*\}'
        metrics = re.search(metrics_pattern, content, re.DOTALL)
        
        if metrics:
            print("Found financial_metrics section")
            old_section = metrics.group(0)
            
            # Add average_interest_rate
            new_section = old_section.rstrip('}') + ',\n'
            new_section += '                "average_interest_rate": {"value": 4.12, "confidence": 0.75, "source": "mock data"}\n'
            new_section += '            }'
            
            # Replace the old section with the new one
            content = content.replace(old_section, new_section)
            print("Added average_interest_rate to financial_metrics")
    
    # Do the same for the other extractors' mock data
    
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