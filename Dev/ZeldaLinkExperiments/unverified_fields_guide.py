#!/usr/bin/env python3
"""
Utility module defining unverified fields to look for in BRF annual reports.
These fields may appear in some reports but are not yet part of the standard schema.
"""

# Dictionary of unverified fields to watch for, organized by category
UNVERIFIED_FIELDS = {
    "property_details": {
        "renovation_year": {
            "description": "Year when major renovations were last performed",
            "type": "string",
            "example": "2018"
        },
        "elevator_available": {
            "description": "Whether the property has elevators",
            "type": "boolean",
            "example": True
        },
        "parking_spaces": {
            "description": "Number of parking spaces and their types",
            "type": "object",
            "example": {"garage": 15, "open": 10, "total": 25}
        },
        "energy_classification": {
            "description": "Environmental rating/energy efficiency class",
            "type": "string",
            "example": "C"
        },
        "heating_system": {
            "description": "Type of heating system used",
            "type": "string",
            "example": "Fjärrvärme"
        }
    },
    "financial_metrics": {
        "maintenance_fund": {
            "description": "Amount set aside for future maintenance",
            "type": "number",
            "example": 3500000
        },
        "budget_next_year": {
            "description": "Upcoming year's budget figures",
            "type": "object",
            "example": {"revenue": 5200000, "expenses": 3800000}
        },
        "debt_ratio": {
            "description": "Total debt relative to property value",
            "type": "number",
            "example": 0.65
        },
        "interest_rate_history": {
            "description": "History of interest rate changes",
            "type": "object",
            "example": {"2021": 2.85, "2022": 3.25, "2023": 3.95}
        },
        "cash_liquidity": {
            "description": "Available cash and short-term assets",
            "type": "number",
            "example": 1250000
        }
    },
    "governance": {
        "annual_meeting_date": {
            "description": "When the last annual meeting was held",
            "type": "string",
            "example": "2023-05-15"
        },
        "external_auditor": {
            "description": "Professional auditing company information",
            "type": "object",
            "example": {"name": "KPMG", "auditor": "Anna Svensson"}
        },
        "board_meeting_frequency": {
            "description": "How often the board meets",
            "type": "number",
            "example": 12
        },
        "property_management": {
            "description": "External property management company",
            "type": "string",
            "example": "Fastighetsägarna Service Stockholm AB"
        }
    },
    "maintenance_planning": {
        "maintenance_plan_period": {
            "description": "How many years the current plan covers",
            "type": "number",
            "example": 30
        },
        "upcoming_renovations": {
            "description": "Specific large projects planned",
            "type": "array",
            "example": ["Fasadrenovering 2025", "Byte av tvättmaskiner 2024"]
        },
        "completed_projects": {
            "description": "Recently completed major work",
            "type": "array",
            "example": ["Renovering av trapphus 2022", "Byte av värmesystem 2021"]
        },
        "deferred_maintenance": {
            "description": "Postponed maintenance needs",
            "type": "array",
            "example": ["Fasadrenovering", "Takunderhåll"]
        }
    },
    "member_information": {
        "ownership_transfers": {
            "description": "Number of apartment sales/transfers in past year",
            "type": "number",
            "example": 5
        },
        "fee_history": {
            "description": "History of monthly fee changes",
            "type": "object",
            "example": {"2021": 650, "2022": 680, "2023": 700}
        },
        "apartment_distribution": {
            "description": "Breakdown of apartment sizes",
            "type": "object",
            "example": {"1 rum": 5, "2 rum": 15, "3 rum": 12, "4+ rum": 8}
        }
    }
}

def generate_prompt_section():
    """Generate a section for the extraction prompt to look for unverified fields."""
    prompt = "\nADDITIONAL FIELD DETECTION:\n"
    prompt += "In addition to the standard schema fields, look for these potential fields that may appear in some reports:\n\n"
    
    for category, fields in UNVERIFIED_FIELDS.items():
        prompt += f"Category: {category.upper()}\n"
        for field_name, details in fields.items():
            prompt += f"- {field_name}: {details['description']} (Example: {details['example']})\n"
        prompt += "\n"
    
    prompt += "If you find any of these fields in the document, please include them in your schema improvement suggestions.\n"
    return prompt

if __name__ == "__main__":
    # Print the prompt section for testing
    print(generate_prompt_section())