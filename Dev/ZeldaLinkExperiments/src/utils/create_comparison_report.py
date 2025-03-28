#!/usr/bin/env python3
"""
Generate a comparison report of LLM extraction results

This script analyzes the results from different LLMs (Claude, GPT-4, Mistral)
on the extraction task and generates an HTML report.
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_test_results(results_dir):
    """Get all test results from the specified directory."""
    test_dirs = [d for d in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, d))]
    
    results = {}
    for test_dir in test_dirs:
        test_path = os.path.join(results_dir, test_dir)
        
        # Get model results
        claude_result = load_json_file(os.path.join(test_path, "claude_extraction.json"))
        gpt4_result = load_json_file(os.path.join(test_path, "gpt4_extraction.json"))
        mistral_result = load_json_file(os.path.join(test_path, "mistral_extraction.json"))
        
        # Get metadata
        summary = load_json_file(os.path.join(test_path, "comparison_summary.json"))
        
        # Skip this directory if we don't have any results
        if not gpt4_result and not mistral_result and not claude_result:
            print(f"Skipping {test_dir}: No extraction results found")
            continue
            
        # Skip if no summary
        if not summary:
            print(f"Skipping {test_dir}: No comparison summary found")
            continue
        
        results[test_dir] = {
            "claude": claude_result or {},
            "gpt4": gpt4_result or {},
            "mistral": mistral_result or {},
            "summary": summary
        }
    
    return results

def format_value(value):
    """Format value for display in HTML table."""
    if value is None:
        return "<em class='missing'>null</em>"
    elif isinstance(value, float):
        return f"{value:,.2f}"
    elif isinstance(value, int):
        return f"{value:,}"
    else:
        return str(value)

def format_confidence(value):
    """Format confidence value with appropriate color."""
    if value is None or value == "":
        return "<span class='confidence-missing'>unknown</span>"
    elif value.lower() == "high":
        return "<span class='confidence-high'>high</span>"
    elif value.lower() == "medium":
        return "<span class='confidence-medium'>medium</span>"
    elif value.lower() == "low":
        return "<span class='confidence-low'>low</span>"
    else:
        return value

def generate_property_info_table(results):
    """Generate an HTML table for property info comparison."""
    html = "<h3>Property Information</h3>"
    html += "<table class='comparison-table'>"
    html += "<tr><th>Field</th><th>Claude</th><th>GPT-4</th><th>Mistral</th></tr>"
    
    fields = ["designation", "organization_number", "address", "total_area", "residential_area", "year_built"]
    
    for field in fields:
        html += f"<tr><td class='field-name'>{field}</td>"
        
        # Claude value
        claude_value = results.get("claude", {}).get("property_info", {}).get(field)
        claude_confidence = results.get("claude", {}).get("property_info", {}).get("confidence", {}).get(field)
        if isinstance(claude_confidence, str):
            html += f"<td>{format_value(claude_value)} <span class='confidence'>({format_confidence(claude_confidence)})</span></td>"
        else:
            # Handle nested confidence structure
            confidence = results.get("claude", {}).get("confidence", {}).get("property_info", {}).get(field)
            html += f"<td>{format_value(claude_value)} <span class='confidence'>({format_confidence(confidence)})</span></td>"
        
        # GPT-4 value
        gpt4_value = results.get("gpt4", {}).get("property_info", {}).get(field)
        gpt4_confidence = None
        if isinstance(results.get("gpt4", {}).get("property_info", {}).get("confidence"), dict):
            gpt4_confidence = results.get("gpt4", {}).get("property_info", {}).get("confidence", {}).get(field)
        html += f"<td>{format_value(gpt4_value)} <span class='confidence'>({format_confidence(gpt4_confidence)})</span></td>"
        
        # Mistral value
        mistral_value = results.get("mistral", {}).get("property_info", {}).get(field)
        mistral_confidence = None
        confidence_section = results.get("mistral", {}).get("confidence_levels", {}).get("property_info", {})
        if confidence_section:
            mistral_confidence = confidence_section.get(field)
        html += f"<td>{format_value(mistral_value)} <span class='confidence'>({format_confidence(mistral_confidence)})</span></td>"
        
        html += "</tr>"
    
    html += "</table>"
    return html

def generate_financial_info_table(results):
    """Generate an HTML table for financial info comparison."""
    html = "<h3>Financial Information</h3>"
    html += "<table class='comparison-table'>"
    html += "<tr><th>Field</th><th>Claude</th><th>GPT-4</th><th>Mistral</th></tr>"
    
    fields = ["total_revenue", "total_expenses", "profit_loss", "monthly_fee"]
    
    for field in fields:
        html += f"<tr><td class='field-name'>{field}</td>"
        
        # Claude value
        claude_value = results.get("claude", {}).get("financial_info", {}).get(field)
        claude_confidence = results.get("claude", {}).get("financial_info", {}).get("confidence", {}).get(field)
        html += f"<td>{format_value(claude_value)} <span class='confidence'>({format_confidence(claude_confidence)})</span></td>"
        
        # GPT-4 value
        gpt4_value = results.get("gpt4", {}).get("financial_info", {}).get(field)
        gpt4_confidence = None
        if isinstance(results.get("gpt4", {}).get("financial_info", {}).get("confidence"), dict):
            gpt4_confidence = results.get("gpt4", {}).get("financial_info", {}).get("confidence", {}).get(field)
        html += f"<td>{format_value(gpt4_value)} <span class='confidence'>({format_confidence(gpt4_confidence)})</span></td>"
        
        # Mistral value
        mistral_value = results.get("mistral", {}).get("financial_info", {}).get(field)
        mistral_confidence = None
        confidence_section = results.get("mistral", {}).get("confidence_levels", {}).get("financial_info", {})
        if confidence_section:
            mistral_confidence = confidence_section.get(field)
        html += f"<td>{format_value(mistral_value)} <span class='confidence'>({format_confidence(mistral_confidence)})</span></td>"
        
        html += "</tr>"
    
    html += "</table>"
    return html

def generate_costs_table(results):
    """Generate an HTML table for costs comparison."""
    html = "<h3>Costs</h3>"
    html += "<table class='comparison-table'>"
    html += "<tr><th>Field</th><th>Claude</th><th>GPT-4</th><th>Mistral</th></tr>"
    
    fields = ["heating", "electricity", "water", "maintenance", "property_tax"]
    
    for field in fields:
        html += f"<tr><td class='field-name'>{field}</td>"
        
        # Claude value
        claude_value = results.get("claude", {}).get("costs", {}).get(field)
        claude_confidence = results.get("claude", {}).get("costs", {}).get("confidence", {}).get(field)
        html += f"<td>{format_value(claude_value)} <span class='confidence'>({format_confidence(claude_confidence)})</span></td>"
        
        # GPT-4 value
        gpt4_value = results.get("gpt4", {}).get("costs", {}).get(field)
        gpt4_confidence = None
        if isinstance(results.get("gpt4", {}).get("costs", {}).get("confidence"), dict):
            gpt4_confidence = results.get("gpt4", {}).get("costs", {}).get("confidence", {}).get(field)
        html += f"<td>{format_value(gpt4_value)} <span class='confidence'>({format_confidence(gpt4_confidence)})</span></td>"
        
        # Mistral value
        mistral_value = results.get("mistral", {}).get("costs", {}).get(field)
        mistral_confidence = None
        confidence_section = results.get("mistral", {}).get("confidence_levels", {}).get("costs", {})
        if confidence_section:
            mistral_confidence = confidence_section.get(field)
        html += f"<td>{format_value(mistral_value)} <span class='confidence'>({format_confidence(mistral_confidence)})</span></td>"
        
        html += "</tr>"
    
    html += "</table>"
    return html

def generate_board_members_table(results):
    """Generate an HTML table for board members comparison."""
    html = "<h3>Board Members</h3>"
    
    claude_members = results.get("claude", {}).get("board_members", [])
    gpt4_members = results.get("gpt4", {}).get("board_members", [])
    mistral_members = results.get("mistral", {}).get("board_members", [])
    
    if not claude_members and not gpt4_members and not mistral_members:
        return html + "<p>No board members found in this extraction.</p>"
    
    html += "<table class='comparison-table'>"
    html += "<tr><th>Claude</th><th>GPT-4</th><th>Mistral</th></tr>"
    
    # Find the model with the most members
    max_members = max(len(claude_members), len(gpt4_members), len(mistral_members))
    
    for i in range(max_members):
        html += "<tr>"
        
        # Claude member
        if i < len(claude_members):
            member = claude_members[i]
            name = member.get("name", "")
            position = member.get("position", "")
            confidence = member.get("confidence", "")
            html += f"<td>{name} - {position} <span class='confidence'>({format_confidence(confidence)})</span></td>"
        else:
            html += "<td class='empty'></td>"
        
        # GPT-4 member
        if i < len(gpt4_members):
            member = gpt4_members[i]
            name = member.get("name", "")
            position = member.get("position", "")
            confidence = member.get("confidence", "")
            html += f"<td>{name} - {position} <span class='confidence'>({format_confidence(confidence)})</span></td>"
        else:
            html += "<td class='empty'></td>"
        
        # Mistral member
        if i < len(mistral_members):
            member = mistral_members[i]
            name = member.get("name", "")
            position = member.get("position", "")
            confidence = member.get("confidence", "")
            html += f"<td>{name} - {position} <span class='confidence'>({format_confidence(confidence)})</span></td>"
        else:
            html += "<td class='empty'></td>"
        
        html += "</tr>"
    
    html += "</table>"
    return html

def generate_loans_table(results):
    """Generate an HTML table for loans comparison."""
    html = "<h3>Loans</h3>"
    
    claude_loans = results.get("claude", {}).get("loans", [])
    gpt4_loans = results.get("gpt4", {}).get("loans", [])
    mistral_loans = results.get("mistral", {}).get("loans", [])
    
    if not claude_loans and not gpt4_loans and not mistral_loans:
        return html + "<p>No loans found in this extraction.</p>"
    
    # Check if all the loan arrays are empty
    if (all(not loan for loan in claude_loans) and 
        all(not loan for loan in gpt4_loans) and 
        all(not loan for loan in mistral_loans)):
        return html + "<p>No loans found in this extraction.</p>"
    
    html += "<table class='comparison-table'>"
    html += "<tr><th colspan='4'>Claude</th><th colspan='4'>GPT-4</th><th colspan='4'>Mistral</th></tr>"
    html += "<tr><th>Lender</th><th>Amount</th><th>Rate</th><th>Term</th><th>Lender</th><th>Amount</th><th>Rate</th><th>Term</th><th>Lender</th><th>Amount</th><th>Rate</th><th>Term</th></tr>"
    
    # Find the model with the most loans
    max_loans = max(len(claude_loans), len(gpt4_loans), len(mistral_loans))
    
    for i in range(max_loans):
        html += "<tr>"
        
        # Claude loan
        if i < len(claude_loans):
            loan = claude_loans[i]
            lender = loan.get("lender", "")
            amount = format_value(loan.get("amount"))
            rate = format_value(loan.get("interest_rate"))
            term = loan.get("term", "")
            html += f"<td>{lender}</td><td>{amount}</td><td>{rate}</td><td>{term}</td>"
        else:
            html += "<td class='empty'></td><td class='empty'></td><td class='empty'></td><td class='empty'></td>"
        
        # GPT-4 loan
        if i < len(gpt4_loans):
            loan = gpt4_loans[i]
            lender = loan.get("lender", "")
            amount = format_value(loan.get("amount"))
            rate = format_value(loan.get("interest_rate"))
            term = loan.get("term", "")
            html += f"<td>{lender}</td><td>{amount}</td><td>{rate}</td><td>{term}</td>"
        else:
            html += "<td class='empty'></td><td class='empty'></td><td class='empty'></td><td class='empty'></td>"
        
        # Mistral loan
        if i < len(mistral_loans):
            loan = mistral_loans[i]
            lender = loan.get("lender", "")
            amount = format_value(loan.get("amount"))
            rate = format_value(loan.get("interest_rate"))
            term = loan.get("term", "")
            html += f"<td>{lender}</td><td>{amount}</td><td>{rate}</td><td>{term}</td>"
        else:
            html += "<td class='empty'></td><td class='empty'></td><td class='empty'></td><td class='empty'></td>"
        
        html += "</tr>"
    
    html += "</table>"
    return html

def generate_performance_table(results):
    """Generate a performance comparison table."""
    summary = results.get("summary", {})
    metrics = summary.get("comparison_metrics", {})
    
    html = "<h3>Performance Metrics</h3>"
    html += "<table class='performance-table'>"
    html += "<tr><th>Model</th><th>Duration (seconds)</th><th>Tokens Used</th><th>Status</th></tr>"
    
    # Claude metrics
    claude_metrics = metrics.get("claude", {})
    html += "<tr><td>Claude</td>"
    if "error" in claude_metrics:
        html += f"<td colspan='2' class='error'>{claude_metrics['error']}</td><td class='status-failed'>Failed</td>"
    else:
        duration = claude_metrics.get("duration_seconds", 0)
        tokens = claude_metrics.get("tokens_used", 0)
        html += f"<td>{duration:.2f}</td><td>{tokens}</td><td class='status-success'>Success</td>"
    html += "</tr>"
    
    # GPT-4 metrics
    gpt4_metrics = metrics.get("gpt4", {})
    html += "<tr><td>GPT-4</td>"
    if "error" in gpt4_metrics:
        html += f"<td colspan='2' class='error'>{gpt4_metrics['error']}</td><td class='status-failed'>Failed</td>"
    else:
        duration = gpt4_metrics.get("duration_seconds", 0)
        tokens = gpt4_metrics.get("tokens_used", 0)
        html += f"<td>{duration:.2f}</td><td>{tokens}</td><td class='status-success'>Success</td>"
    html += "</tr>"
    
    # Mistral Large metrics
    mistral_metrics = metrics.get("mistral", {})
    html += "<tr><td>Mistral Large</td>"
    if "error" in mistral_metrics:
        html += f"<td colspan='2' class='error'>{mistral_metrics['error']}</td><td class='status-failed'>Failed</td>"
    else:
        duration = mistral_metrics.get("duration_seconds", 0)
        tokens = mistral_metrics.get("tokens_used", 0)
        html += f"<td>{duration:.2f}</td><td>{tokens}</td><td class='status-success'>Success</td>"
    html += "</tr>"
    
    # Mistral Small metrics
    mistral_small_metrics = metrics.get("mistral_small", {})
    if mistral_small_metrics:  # Only show if data exists
        html += "<tr><td>Mistral Small</td>"
        if "error" in mistral_small_metrics:
            html += f"<td colspan='2' class='error'>{mistral_small_metrics['error']}</td><td class='status-failed'>Failed</td>"
        else:
            duration = mistral_small_metrics.get("duration_seconds", 0)
            tokens = mistral_small_metrics.get("tokens_used", 0)
            html += f"<td>{duration:.2f}</td><td>{tokens}</td><td class='status-success'>Success</td>"
        html += "</tr>"
    
    html += "</table>"
    return html

def generate_test_section(test_name, test_results):
    """Generate an HTML section for a single test."""
    # Determine the test type from the name
    test_type = "unknown"
    if "board_members" in test_name:
        test_type = "Board Members"
    elif "financial" in test_name:
        test_type = "Financial Information"
    elif "property_info" in test_name:
        test_type = "Property Information"
    elif "loan_info" in test_name:
        test_type = "Loan Information"
    
    # Get document name
    doc_name = "Unknown"
    if test_name.startswith("tradgarden"):
        doc_name = "Tradgården BRF"
    elif test_name.startswith("sailor"):
        doc_name = "Sailor BRF"
    elif test_name.startswith("forma"):
        doc_name = "Forma BRF"
    
    html = f"<div class='test-section' id='{test_name}'>"
    html += f"<h2>{doc_name} - {test_type}</h2>"
    
    # Performance metrics
    html += generate_performance_table(test_results)
    
    # Data extraction results
    html += generate_property_info_table(test_results)
    html += generate_financial_info_table(test_results)
    html += generate_costs_table(test_results)
    html += generate_board_members_table(test_results)
    html += generate_loans_table(test_results)
    
    html += "</div>"
    return html

def generate_html_report(results, output_file):
    """Generate the full HTML report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>LLM Extraction Comparison Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2980b9;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        h3 {{
            color: #3498db;
            margin-top: 20px;
        }}
        .test-section {{
            border: 1px solid #ddd;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .comparison-table, .performance-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .comparison-table th, .performance-table th,
        .comparison-table td, .performance-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .comparison-table th, .performance-table th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        .field-name {{
            font-weight: bold;
            background-color: #f9f9f9;
        }}
        .confidence {{
            font-size: 0.8em;
            color: #666;
        }}
        .confidence-high {{
            color: #27ae60;
            font-weight: bold;
        }}
        .confidence-medium {{
            color: #f39c12;
        }}
        .confidence-low {{
            color: #e74c3c;
        }}
        .confidence-missing {{
            color: #7f8c8d;
            font-style: italic;
        }}
        .missing {{
            color: #7f8c8d;
            font-style: italic;
        }}
        .empty {{
            background-color: #f9f9f9;
        }}
        .error {{
            color: #e74c3c;
            font-style: italic;
        }}
        .status-success {{
            color: #27ae60;
            font-weight: bold;
        }}
        .status-failed {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .toc {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 20px;
        }}
        .toc a {{
            text-decoration: none;
            color: #3498db;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        .metadata {{
            font-style: italic;
            color: #7f8c8d;
            margin-top: 10px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>LLM Extraction Comparison Report</h1>
    <p class="metadata">Generated on {now}</p>
    
    <div class="toc">
        <h3>Table of Contents</h3>
        <ul>
"""

    # Generate table of contents
    for test_name in results.keys():
        # Get document name
        doc_name = "Unknown"
        if test_name.startswith("tradgarden"):
            doc_name = "Tradgården BRF"
        elif test_name.startswith("sailor"):
            doc_name = "Sailor BRF"
        elif test_name.startswith("forma"):
            doc_name = "Forma BRF"
        
        # Determine the test type from the name
        test_type = "unknown"
        if "board_members" in test_name:
            test_type = "Board Members"
        elif "financial" in test_name:
            test_type = "Financial Information"
        elif "property_info" in test_name:
            test_type = "Property Information"
        elif "loan_info" in test_name:
            test_type = "Loan Information"
        
        html += f"            <li><a href='#{test_name}'>{doc_name} - {test_type}</a></li>\n"
    
    html += """        </ul>
    </div>
"""

    # Generate test sections
    for test_name, test_results in results.items():
        html += generate_test_section(test_name, test_results)
    
    html += """    <div class="metadata">
        <p>This report compares the extraction capabilities of Claude, GPT-4, and Mistral models on Swedish housing association (BRF) annual report data.</p>
    </div>
</body>
</html>"""

    # Write the HTML to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Report generated successfully: {output_file}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate a comparison report of LLM extraction results")
    parser.add_argument("--results-dir", "-r", default="./llm_sample_results", help="Directory containing test results")
    parser.add_argument("--output", "-o", default="./llm_comparison_report.html", help="Output HTML file path")
    
    args = parser.parse_args()
    
    # Get test results
    results = get_test_results(args.results_dir)
    
    # Generate HTML report
    generate_html_report(results, args.output)

if __name__ == "__main__":
    main()