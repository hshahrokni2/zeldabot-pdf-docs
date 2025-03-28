#!/usr/bin/env python3
"""Update financial metrics in extraction prompts with average_interest_rate field."""

import os
import re
from pathlib import Path

def update_financial_metrics(file_path):
    print(f"Reading file: {file_path}")
    # Create backup first
    backup_path = f"{file_path}.bak2"
    os.system(f"cp {file_path} {backup_path}")
    print(f"Created backup at: {backup_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # First, check if the changes have already been applied
    if '"average_interest_rate"' in content:
        print("Financial metrics update already applied")
        return True
    
    print("Updating financial_metrics sections...")
    # Update specific financial_metrics sections by pattern matching
    pattern = r'"financial_metrics": \{[\s\S]*?"total_debt": \{"value": number, "confidence": float, "source": string\}[\s\S]*?\},'
    matches = re.findall(pattern, content)
    
    if not matches:
        print("No financial_metrics sections found!")
        return False
    
    for match in matches:
        new_match = match.replace(
            '"total_debt": {"value": number, "confidence": float, "source": string}',
            '"total_debt": {"value": number, "confidence": float, "source": string},\n            "average_interest_rate": {"value": number, "confidence": float, "source": string}'
        )
        content = content.replace(match, new_match)
    
    print("Writing updated content to file...")
    with open(file_path, 'w') as f:
        f.write(content)
    
    return True

if __name__ == "__main__":
    file_path = Path("/Users/hosseins/Dev/ZeldaLinkExperiments/src/extraction/extract.py")
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        exit(1)
    
    success = update_financial_metrics(str(file_path))
    if success:
        print("Updated financial metrics in all extractor prompts successfully!")
    else:
        print("Failed to update financial metrics.")