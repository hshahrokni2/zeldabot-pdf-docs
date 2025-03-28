#!/usr/bin/env python3
"""
LLM Extraction Comparison Tool

This script compares the extraction capabilities of Claude 3.7, GPT-4, and Mistral-Large
on Swedish housing association (BRF) annual report data from OCR text.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Import necessary packages
try:
    from mistralai import Mistral
    from openai import OpenAI
    from anthropic import Anthropic
except ImportError:
    print("Installing required SDK packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mistralai", "openai", "anthropic", "--break-system-packages"])
    from mistralai import Mistral
    from openai import OpenAI
    from anthropic import Anthropic

# Constants and environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

def read_ocr_text(file_path):
    """
    Read OCR text from a file.
    
    Args:
        file_path: Path to the OCR text file
        
    Returns:
        OCR text content
    """
    if not os.path.isfile(file_path):
        print(f"Error: OCR file not found at {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading OCR file: {e}")
        return None

def create_extraction_prompt(ocr_text):
    """
    Create a standardized extraction prompt for all models.
    
    Args:
        ocr_text: OCR text to analyze
        
    Returns:
        Formatted extraction prompt
    """
    return f"""
    Analyze this Swedish housing association (BRF) annual report OCR text and extract key data:

    {ocr_text}

    Extract and return the following fields in JSON format:

    1. property_info:
       - designation: Property designation/Fastighetsbeteckning
       - organization_number: Organization number/Organisationsnummer
       - address: Address of the property/Adress
       - total_area: Total area in square meters/Total yta i kvadratmeter
       - residential_area: Residential area in square meters/Bostadsyta (BOA)
       - year_built: Year the property was built/Byggnadsår or year the association was formed
    
    2. financial_info:
       - total_revenue: Total revenue for the reporting year/Totala intäkter
       - total_expenses: Total expenses for the reporting year/Totala kostnader
       - profit_loss: Profit or loss for the year/Årets resultat
       - monthly_fee: Monthly fee per square meter/Månadsavgift per kvm (if available)
    
    3. costs:
       - heating: Heating costs/Värmekostnader
       - electricity: Electricity costs/Elkostnader
       - water: Water and sewage costs/Vatten och avlopp
       - maintenance: Maintenance costs/Underhållskostnader
       - property_tax: Property tax/Fastighetsskatt
    
    4. loans:
       - A list of loans with the following information for each:
         - lender: Name of the lender/Långivare
         - amount: Loan amount/Lånebelopp
         - interest_rate: Interest rate/Räntesats (%)
         - term: Loan term or next refinancing date/Löptid eller omsättningsdatum
    
    5. board_members:
       - A list of board members with their names and positions/roles in the board
    
    IMPORTANT:
    1. Convert all Swedish number formats (e.g., "1 234,56") to standard format (1234.56)
    2. Format all monetary values as numbers without currency symbols or spaces
    3. Include confidence levels (high, medium, low) for each field based on how certain you are
    4. If you can't find a value, use null instead of empty string or 0
    """

def extract_with_mistral(ocr_text):
    """
    Extract data using Mistral Large.
    
    Args:
        ocr_text: OCR text to analyze
        
    Returns:
        Extraction results and timing information
    """
    print("Extracting with Mistral Large...")
    start_time = time.time()
    
    # For demonstration purposes, mock the API call to avoid errors
    if os.getenv("MOCK_APIS", "false").lower() == "true":
        print("Using mock Mistral API response")
        # Simulate API processing time
        time.sleep(2)
        
        # Create mock extraction results
        mock_data = {
            "property_info": {
                "designation": "Gustavsberg 1:71",
                "organization_number": "769636-3808",
                "address": "Gustavsbergsvägen 12, 134 41 Gustavsberg",
                "total_area": 3246,
                "residential_area": 2980,
                "year_built": 2020,
                "confidence": "high"
            },
            "financial_info": {
                "total_revenue": 3788000,
                "total_expenses": 2122900,
                "profit_loss": 952800,
                "monthly_fee": None,
                "confidence": "high"
            },
            "costs": {
                "heating": 421300,
                "electricity": 193200,
                "water": 126700,
                "maintenance": 310000,
                "property_tax": 86100,
                "confidence": "medium"
            },
            "loans": [
                {
                    "lender": "Swedbank",
                    "amount": 10400000,
                    "interest_rate": 3.75,
                    "term": "2024-09-15",
                    "confidence": "high"
                },
                {
                    "lender": "SEB",
                    "amount": 8600000,
                    "interest_rate": 4.25,
                    "term": "2026-03-25",
                    "confidence": "high"
                },
                {
                    "lender": "Handelsbanken",
                    "amount": 7500000,
                    "interest_rate": 3.50,
                    "term": "2025-06-30",
                    "confidence": "high"
                }
            ],
            "board_members": [
                {
                    "name": "Anna Andersson",
                    "position": "Ordförande",
                    "confidence": "high"
                },
                {
                    "name": "Bengt Bengtsson",
                    "position": "Sekreterare",
                    "confidence": "high"
                },
                {
                    "name": "Carl Carlsson",
                    "position": "Kassör",
                    "confidence": "high"
                },
                {
                    "name": "Diana Danielsson",
                    "position": "Ledamot",
                    "confidence": "high"
                },
                {
                    "name": "Erik Eriksson",
                    "position": "Ledamot",
                    "confidence": "high"
                }
            ]
        }
        
        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Add metadata
        mock_data["_metadata"] = {
            "model": "mistral-large-latest (mock)",
            "extraction_timestamp": str(datetime.now()),
            "extraction_duration_seconds": duration,
            "tokens_used": 1234,
            "source": "OCR text extraction benchmark (mock data)"
        }
        
        return {
            "results": mock_data,
            "duration": duration,
            "tokens": 1234,
            "success": True
        }
    
    # Real API call if not mocked
    try:
        client = Mistral(api_key=MISTRAL_API_KEY)
        
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "user",
                    "content": create_extraction_prompt(ocr_text)
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        # Get results
        extracted_data = json.loads(response.choices[0].message.content)
        
        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Add metadata
        extracted_data["_metadata"] = {
            "model": "mistral-large-latest",
            "extraction_timestamp": str(datetime.now()),
            "extraction_duration_seconds": duration,
            "tokens_used": response.usage.total_tokens,
            "source": "OCR text extraction benchmark"
        }
        
        return {
            "results": extracted_data,
            "duration": duration,
            "tokens": response.usage.total_tokens,
            "success": True
        }
    
    except Exception as e:
        print(f"Error extracting with Mistral: {e}")
        end_time = time.time()
        
        return {
            "results": None,
            "duration": end_time - start_time,
            "tokens": 0,
            "success": False,
            "error": str(e)
        }

def extract_with_gpt4(ocr_text):
    """
    Extract data using OpenAI GPT-4.
    
    Args:
        ocr_text: OCR text to analyze
        
    Returns:
        Extraction results and timing information
    """
    print("Extracting with OpenAI GPT-4...")
    start_time = time.time()
    
    # For demonstration purposes, mock the API call to avoid errors
    if os.getenv("MOCK_APIS", "false").lower() == "true":
        print("Using mock GPT-4 API response")
        # Simulate API processing time
        time.sleep(1.5)
        
        # Create mock extraction results
        mock_data = {
            "property_info": {
                "designation": "Gustavsberg 1:71",
                "organization_number": "769636-3808",
                "address": "Gustavsbergsvägen 12, 134 41 Gustavsberg",
                "total_area": 3246,
                "residential_area": 2980,
                "year_built": 2020,
                "confidence": "high"
            },
            "financial_info": {
                "total_revenue": 3788000,
                "total_expenses": 2122900,
                "profit_loss": 952800,
                "monthly_fee": 1164.97,
                "confidence": "high"
            },
            "costs": {
                "heating": 421300,
                "electricity": 193200,
                "water": 126700,
                "maintenance": 310000,
                "property_tax": 86100,
                "confidence": "high"
            },
            "loans": [
                {
                    "lender": "Swedbank",
                    "amount": 10400000,
                    "interest_rate": 3.75,
                    "term": "2024-09-15",
                    "confidence": "high"
                },
                {
                    "lender": "SEB",
                    "amount": 8600000,
                    "interest_rate": 4.25,
                    "term": "2026-03-25",
                    "confidence": "high"
                },
                {
                    "lender": "Handelsbanken",
                    "amount": 7500000,
                    "interest_rate": 3.50,
                    "term": "2025-06-30",
                    "confidence": "high"
                }
            ],
            "board_members": [
                {
                    "name": "Anna Andersson",
                    "position": "Ordförande",
                    "confidence": "high"
                },
                {
                    "name": "Bengt Bengtsson",
                    "position": "Sekreterare",
                    "confidence": "high"
                },
                {
                    "name": "Carl Carlsson",
                    "position": "Kassör",
                    "confidence": "high"
                },
                {
                    "name": "Diana Danielsson",
                    "position": "Ledamot",
                    "confidence": "high"
                },
                {
                    "name": "Erik Eriksson",
                    "position": "Ledamot",
                    "confidence": "high"
                },
                {
                    "name": "Fredrik Fredriksson",
                    "position": "Suppleant",
                    "confidence": "medium"
                },
                {
                    "name": "Gunilla Gustafsson",
                    "position": "Suppleant",
                    "confidence": "medium"
                }
            ]
        }
        
        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Add metadata
        mock_data["_metadata"] = {
            "model": "gpt-4-0125-preview (mock)",
            "extraction_timestamp": str(datetime.now()),
            "extraction_duration_seconds": duration,
            "tokens_used": 1542,
            "source": "OCR text extraction benchmark (mock data)"
        }
        
        return {
            "results": mock_data,
            "duration": duration,
            "tokens": 1542,
            "success": True
        }
    
    # Real API call if not mocked
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",  # Or latest GPT-4 model available
            messages=[
                {
                    "role": "user",
                    "content": create_extraction_prompt(ocr_text)
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        # Get results
        extracted_data = json.loads(response.choices[0].message.content)
        
        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Add metadata
        extracted_data["_metadata"] = {
            "model": "gpt-4-0125-preview",
            "extraction_timestamp": str(datetime.now()),
            "extraction_duration_seconds": duration,
            "tokens_used": response.usage.total_tokens,
            "source": "OCR text extraction benchmark"
        }
        
        return {
            "results": extracted_data,
            "duration": duration,
            "tokens": response.usage.total_tokens,
            "success": True
        }
    
    except Exception as e:
        print(f"Error extracting with GPT-4: {e}")
        end_time = time.time()
        
        return {
            "results": None,
            "duration": end_time - start_time,
            "tokens": 0,
            "success": False,
            "error": str(e)
        }

def extract_with_claude(ocr_text):
    """
    Extract data using Anthropic Claude 3.7.
    
    Args:
        ocr_text: OCR text to analyze
        
    Returns:
        Extraction results and timing information
    """
    print("Extracting with Claude 3.7...")
    start_time = time.time()
    
    # For demonstration purposes, mock the API call to avoid errors
    if os.getenv("MOCK_APIS", "false").lower() == "true":
        print("Using mock Claude API response")
        # Simulate API processing time
        time.sleep(1.2)
        
        # Create mock extraction results - with some variations to show differences
        mock_data = {
            "property_info": {
                "designation": "Gustavsberg 1:71",
                "organization_number": "769636-3808",
                "address": "Gustavsbergsvägen 12, 134 41 Gustavsberg",
                "total_area": 3246,
                "residential_area": 2980,
                "year_built": 2018,  # Different: uses formation year instead of completion
                "confidence": "high"
            },
            "financial_info": {
                "total_revenue": 3788000,
                "total_expenses": 2835200,  # Different: includes financial costs in expenses
                "profit_loss": 952800,
                "monthly_fee": 1165,
                "confidence": "high"
            },
            "costs": {
                "heating": 421300,
                "electricity": 193200,
                "water": 126700,
                "maintenance": 412400,  # Different: combines repairs and maintenance
                "property_tax": 86100,
                "confidence": "high"
            },
            "loans": [
                {
                    "lender": "Swedbank",
                    "amount": 10400000,
                    "interest_rate": 3.75,
                    "term": "2024-09-15",
                    "confidence": "high"
                },
                {
                    "lender": "SEB",
                    "amount": 8600000,
                    "interest_rate": 4.25,
                    "term": "2026-03-25",
                    "confidence": "high"
                },
                {
                    "lender": "Handelsbanken",
                    "amount": 7500000,
                    "interest_rate": 3.50,
                    "term": "2025-06-30",
                    "confidence": "high"
                }
            ],
            "board_members": [
                {
                    "name": "Anna Andersson",
                    "position": "Ordförande",
                    "confidence": "high"
                },
                {
                    "name": "Bengt Bengtsson",
                    "position": "Sekreterare",
                    "confidence": "high"
                },
                {
                    "name": "Carl Carlsson",
                    "position": "Kassör",
                    "confidence": "high"
                },
                {
                    "name": "Diana Danielsson",
                    "position": "Ledamot",
                    "confidence": "high"
                },
                {
                    "name": "Erik Eriksson",
                    "position": "Ledamot",
                    "confidence": "high"
                },
                {
                    "name": "Fredrik Fredriksson",
                    "position": "Suppleant",
                    "confidence": "high"
                },
                {
                    "name": "Gunilla Gustafsson",
                    "position": "Suppleant",
                    "confidence": "high"
                },
                {
                    "name": "Hans Hansson",
                    "position": "Revisor, EY",
                    "confidence": "medium"
                }
            ]
        }
        
        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Add metadata
        mock_data["_metadata"] = {
            "model": "claude-3-sonnet-20240229 (mock)",
            "extraction_timestamp": str(datetime.now()),
            "extraction_duration_seconds": duration,
            "tokens_used": 1738,
            "source": "OCR text extraction benchmark (mock data)"
        }
        
        return {
            "results": mock_data,
            "duration": duration,
            "tokens": 1738,
            "success": True
        }
    
    # Real API call if not mocked
    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",  # Using Claude 3 Sonnet as Claude 3.7 is not widely available yet
            messages=[
                {
                    "role": "user",
                    "content": create_extraction_prompt(ocr_text)
                }
            ],
            temperature=0,
            system="You are an expert in analyzing Swedish financial documents and extracting structured data.",
            max_tokens=4096
        )
        
        # Get results - debug response format first
        content_text = response.content[0].text
        print(f"Claude response content: {content_text}")
        
        try:
            # Check if the response is JSON
            if content_text.strip().startswith("{"):
                extracted_data = json.loads(content_text)
            else:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```json\n(.*?)\n```', content_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group(1))
                else:
                    # Create a minimal valid response
                    extracted_data = {
                        "property_info": {},
                        "financial_info": {},
                        "costs": {},
                        "loans": [],
                        "board_members": [],
                        "error": "Failed to parse Claude response as JSON"
                    }
        except Exception as e:
            print(f"JSON parsing error: {e}")
            print(f"Original content: {content_text}")
            # Create a minimal valid response
            extracted_data = {
                "property_info": {},
                "financial_info": {},
                "costs": {},
                "loans": [],
                "board_members": [],
                "error": f"JSON parsing failed: {str(e)}"
            }
        
        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Add metadata
        extracted_data["_metadata"] = {
            "model": "claude-3-sonnet-20240229",
            "extraction_timestamp": str(datetime.now()),
            "extraction_duration_seconds": duration,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "source": "OCR text extraction benchmark"
        }
        
        return {
            "results": extracted_data,
            "duration": duration,
            "tokens": response.usage.input_tokens + response.usage.output_tokens,
            "success": True
        }
    
    except Exception as e:
        print(f"Error extracting with Claude: {e}")
        end_time = time.time()
        
        return {
            "results": None, 
            "duration": end_time - start_time,
            "tokens": 0,
            "success": False,
            "error": str(e)
        }

def extract_with_mistral_small(ocr_text):
    """
    Extract data using Mistral Small.
    
    Args:
        ocr_text: OCR text to analyze
        
    Returns:
        Extraction results and timing information
    """
    print("Extracting with Mistral Small...")
    start_time = time.time()
    
    # For demonstration purposes, mock the API call to avoid errors
    if os.getenv("MOCK_APIS", "false").lower() == "true":
        print("Using mock Mistral Small API response")
        # Simulate API processing time
        time.sleep(1.0)
        
        # Create mock extraction results - with some variations to show differences
        mock_data = {
            "property_info": {
                "designation": "Gustavsberg 1:71",
                "organization_number": "769636-3808",
                "address": "Gustavsbergsvägen 12, 134 41 Gustavsberg",
                "total_area": 3246,
                "residential_area": 2980,
                "year_built": 2020,
                "confidence": "medium"
            },
            "financial_info": {
                "total_revenue": 3788000,
                "total_expenses": 2122900,
                "profit_loss": 952800,
                "monthly_fee": None,
                "confidence": "medium"
            },
            "costs": {
                "heating": 421300,
                "electricity": 193200,
                "water": 126700,
                "maintenance": 310000,
                "property_tax": 86100,
                "confidence": "low" 
            },
            "loans": [
                {
                    "lender": "Swedbank",
                    "amount": 10400000,
                    "interest_rate": 3.75,
                    "term": "2024-09-15",
                    "confidence": "medium"
                }
            ],
            "board_members": [
                {
                    "name": "Anna Andersson",
                    "position": "Ordförande",
                    "confidence": "medium"
                },
                {
                    "name": "Bengt Bengtsson",
                    "position": "Sekreterare",
                    "confidence": "medium"
                }
            ]
        }
        
        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Add metadata
        mock_data["_metadata"] = {
            "model": "mistral-small-latest (mock)",
            "extraction_timestamp": str(datetime.now()),
            "extraction_duration_seconds": duration,
            "tokens_used": 942,
            "source": "OCR text extraction benchmark (mock data)"
        }
        
        return {
            "results": mock_data,
            "duration": duration,
            "tokens": 942,
            "success": True
        }
    
    # Real API call if not mocked
    try:
        client = Mistral(api_key=MISTRAL_API_KEY)
        
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {
                    "role": "user",
                    "content": create_extraction_prompt(ocr_text)
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        # Get results
        extracted_data = json.loads(response.choices[0].message.content)
        
        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Add metadata
        extracted_data["_metadata"] = {
            "model": "mistral-small-latest",
            "extraction_timestamp": str(datetime.now()),
            "extraction_duration_seconds": duration,
            "tokens_used": response.usage.total_tokens,
            "source": "OCR text extraction benchmark"
        }
        
        return {
            "results": extracted_data,
            "duration": duration,
            "tokens": response.usage.total_tokens,
            "success": True
        }
    
    except Exception as e:
        print(f"Error extracting with Mistral Small: {e}")
        end_time = time.time()
        
        return {
            "results": None,
            "duration": end_time - start_time,
            "tokens": 0,
            "success": False,
            "error": str(e)
        }

def run_comparison(ocr_text, output_dir):
    """
    Run extraction comparison across all models.
    
    Args:
        ocr_text: OCR text to analyze
        output_dir: Directory to save results
        
    Returns:
        Comparison results
    """
    results = {}
    summary = {
        "timestamp": str(datetime.now()),
        "models_compared": ["claude-3-sonnet", "gpt-4", "mistral-large", "mistral-small"],
        "comparison_metrics": {}
    }
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Test each model if API key is available
    if ANTHROPIC_API_KEY:
        claude_results = extract_with_claude(ocr_text)
        results["claude"] = claude_results
        
        # Save individual results
        if claude_results["success"]:
            with open(os.path.join(output_dir, "claude_extraction.json"), 'w', encoding='utf-8') as f:
                json.dump(claude_results["results"], f, ensure_ascii=False, indent=2)
    else:
        print("Skipping Claude extraction - no API key provided")
        results["claude"] = {"success": False, "error": "No API key provided"}
    
    if OPENAI_API_KEY:
        gpt4_results = extract_with_gpt4(ocr_text)
        results["gpt4"] = gpt4_results
        
        # Save individual results
        if gpt4_results["success"]:
            with open(os.path.join(output_dir, "gpt4_extraction.json"), 'w', encoding='utf-8') as f:
                json.dump(gpt4_results["results"], f, ensure_ascii=False, indent=2)
    else:
        print("Skipping GPT-4 extraction - no API key provided")
        results["gpt4"] = {"success": False, "error": "No API key provided"}
    
    if MISTRAL_API_KEY:
        # Mistral Large
        mistral_results = extract_with_mistral(ocr_text)
        results["mistral"] = mistral_results
        
        # Save individual results
        if mistral_results["success"]:
            with open(os.path.join(output_dir, "mistral_extraction.json"), 'w', encoding='utf-8') as f:
                json.dump(mistral_results["results"], f, ensure_ascii=False, indent=2)
                
        # Mistral Small
        mistral_small_results = extract_with_mistral_small(ocr_text)
        results["mistral_small"] = mistral_small_results
        
        # Save individual results
        if mistral_small_results["success"]:
            with open(os.path.join(output_dir, "mistral_small_extraction.json"), 'w', encoding='utf-8') as f:
                json.dump(mistral_small_results["results"], f, ensure_ascii=False, indent=2)
    else:
        print("Skipping Mistral extraction - no API key provided")
        results["mistral"] = {"success": False, "error": "No API key provided"}
        results["mistral_small"] = {"success": False, "error": "No API key provided"}
    
    # Create comparison summary
    for model, model_results in results.items():
        if model_results["success"]:
            summary["comparison_metrics"][model] = {
                "duration_seconds": model_results["duration"],
                "tokens_used": model_results["tokens"]
            }
        else:
            summary["comparison_metrics"][model] = {
                "error": model_results.get("error", "Unknown error")
            }
    
    # Save comparison summary
    with open(os.path.join(output_dir, "comparison_summary.json"), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    return results, summary

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Compare LLM extraction capabilities on OCR text")
    parser.add_argument("--ocr", "-i", required=True, help="Path to the OCR text file")
    parser.add_argument("--output-dir", "-o", default="extraction_comparison", help="Directory to save extraction results")
    parser.add_argument("--selected-pages", action="store_true", help="Use only selected pages instead of full document")
    
    args = parser.parse_args()
    
    # Read OCR text
    ocr_text = read_ocr_text(args.ocr)
    if not ocr_text:
        return 1
    
    # Extract selected pages if requested
    if args.selected_pages:
        # This is a simplified approach - in practice, you'd want a more sophisticated page selection
        # Here we're just grabbing pages that likely contain board members and financial tables
        print("Extracting selected pages only...")
        
        try:
            ocr_data = json.loads(ocr_text)
            selected_pages = []
            
            # Look for pages with board members (typically in the first few pages)
            for page in ocr_data["pages"][:5]:
                if any(keyword in page["text"].lower() for keyword in ["styrelse", "board", "ledamöter", "ordförande"]):
                    selected_pages.append(page)
            
            # Look for pages with financial tables (using keywords)
            for page in ocr_data["pages"]:
                if any(keyword in page["text"].lower() for keyword in ["resultaträkning", "balansräkning", "income statement", "balance sheet"]):
                    if page not in selected_pages:
                        selected_pages.append(page)
            
            # Create a new OCR document with just the selected pages
            selected_ocr = {
                "document_id": ocr_data.get("document_id", "selected-pages"),
                "pages": selected_pages
            }
            
            # Convert back to string
            ocr_text = json.dumps(selected_ocr, ensure_ascii=False)
            print(f"Selected {len(selected_pages)} pages for analysis")
            
        except json.JSONDecodeError:
            print("Warning: OCR text is not in JSON format, using full document")
    
    # Run comparison
    results, summary = run_comparison(ocr_text, args.output_dir)
    
    # Display quick summary
    print("\nExtraction Comparison Summary:")
    print("===============================")
    
    for model, metrics in summary["comparison_metrics"].items():
        print(f"\n{model.upper()}:")
        if "error" in metrics:
            print(f"  Error: {metrics['error']}")
        else:
            print(f"  Duration: {metrics['duration_seconds']:.2f} seconds")
            if "tokens" in metrics:
                print(f"  Tokens used: {metrics['tokens']}")
    
    print(f"\nResults saved to: {args.output_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())