#!/usr/bin/env python3
"""Update all extractor prompts with new schema fields."""

import os
import re
from pathlib import Path

def update_extractor_prompts(file_path):
    print(f"Reading file: {file_path}")
    # Create backup first
    backup_path = f"{file_path}.bak"
    os.system(f"cp {file_path} {backup_path}")
    print(f"Created backup at: {backup_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # First, check if the changes have already been applied
    if '"average_interest_rate"' in content:
        print("Financial metrics update already applied")
    else:
        print("Updating financial_metrics sections...")
        # Update financial_metrics sections with average_interest_rate
        content = content.replace(
            '"total_debt": {"value": number, "confidence": float, "source": string}',
            '"total_debt": {"value": number, "confidence": float, "source": string},\n            "average_interest_rate": {"value": number, "confidence": float, "source": string}'
        )
    
    # Find all income statement sections that don't have previous_year fields
    if '"previous_year_revenue"' in content:
        print("Income statement update already applied")
    else:
        print("Updating income_statement sections...")
        # Update each income statement section - using a more specific approach
        sections = re.findall(r'("income_statement": \{\s+.*?"expense_breakdown": \{.*?\}\s+\})', content, re.DOTALL)
        
        for section in sections:
            if '"previous_year_revenue"' not in section:
                new_section = section.rstrip('}') + ',\n'
                new_section += '              "previous_year_revenue": {"value": number, "confidence": float, "source": string},\n'
                new_section += '              "previous_year_expenses": {"value": number, "confidence": float, "source": string},\n'
                new_section += '              "previous_year_net_income": {"value": number, "confidence": float, "source": string},\n'
                new_section += '              "previous_year_revenue_breakdown": {\n'
                new_section += '                "annual_fees": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "rental_income": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "other_income": {"value": number, "confidence": float, "source": string}\n'
                new_section += '              },\n'
                new_section += '              "previous_year_expense_breakdown": {\n'
                new_section += '                "electricity": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "heating": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "water_and_sewage": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "waste_management": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "property_maintenance": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "repairs": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "maintenance": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "property_tax": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "property_insurance": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "cable_tv_internet": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "board_costs": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "management_fees": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "other_operating_costs": {"value": number, "confidence": float, "source": string},\n'
                new_section += '                "financial_costs": {"value": number, "confidence": float, "source": string}\n'
                new_section += '              }'
                
                content = content.replace(section, new_section)
    
    print("Writing updated content to file...")
    with open(file_path, 'w') as f:
        f.write(content)
    
    return True

if __name__ == "__main__":
    file_path = Path("/Users/hosseins/Dev/ZeldaLinkExperiments/src/extraction/extract.py")
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        exit(1)
    
    success = update_extractor_prompts(str(file_path))
    if success:
        print("Updated all extractor prompts successfully!")
    else:
        print("Failed to update extractor prompts.")