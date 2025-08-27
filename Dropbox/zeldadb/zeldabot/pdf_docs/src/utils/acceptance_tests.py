#!/usr/bin/env python3
"""
Acceptance Tests - Hard gates with Sjöstaden 2 canaries
Numeric validation with tolerances, fail-fast policy
"""
import os
import sys
import json
import psycopg2
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path

# Sjöstaden 2 (2024) ground truth canaries - IMMUTABLE
CANARY_GATES = {
    "document_identifier": "BRF Sjöstaden 2",
    "year": 2024,
    "total_assets": 301339818,      # SEK
    "total_debt": 99538124,         # SEK  
    "cash_closing": 7335586,        # SEK
    "org_number": "769606-2533",
    "chairman": "Rolf Johansson",
    "auditor_name": "Katarina Nyberg",
    "audit_firm": "HQV Stockholm AB",
    "property_name": "Brädgården 9"
}

# Tolerances
TOLERANCE_PERCENT = 0.01  # ±1%
TOLERANCE_SEK = 5000      # ±5k SEK

def normalize_name(name: str) -> str:
    """Normalize names for comparison"""
    if not name:
        return ""
    return name.strip().lower().replace("  ", " ")

def check_numeric_tolerance(actual: float, expected: float, label: str) -> Optional[str]:
    """Check if numeric value is within tolerance"""
    if actual == 0 and expected != 0:
        return f"{label}: got 0, expected {expected:,}"
    
    if expected == 0:
        if actual != 0:
            return f"{label}: expected 0, got {actual:,}"
        return None
    
    # Percentage tolerance
    percent_diff = abs(actual - expected) / expected
    if percent_diff > TOLERANCE_PERCENT:
        # Also check absolute tolerance
        abs_diff = abs(actual - expected)
        if abs_diff > TOLERANCE_SEK:
            return f"{label}: expected {expected:,}, got {actual:,} (diff: {abs_diff:,} SEK, {percent_diff:.2%})"
    
    return None

def run_acceptance_gates(results: Dict[str, Any]) -> Dict[str, Any]:
    """Run acceptance gates against extraction results"""
    gates_status = {
        "gates_passed": True,
        "failures": [],
        "checks_performed": 0,
        "timestamp": "2025-08-27T12:00:00Z"  # Would use actual timestamp
    }
    
    # Financial checks
    if "balance_sheet" in results:
        bs = results["balance_sheet"]
        gates_status["checks_performed"] += 1
        
        # Assets check
        actual_assets = float(bs.get("total_assets", 0))
        error = check_numeric_tolerance(actual_assets, CANARY_GATES["total_assets"], "Total Assets")
        if error:
            gates_status["failures"].append(error)
            gates_status["gates_passed"] = False
        
        # Debt check (try multiple field names)
        actual_debt = float(bs.get("loans", 0) or bs.get("total_debt", 0) or bs.get("long_term_debt", 0))
        error = check_numeric_tolerance(actual_debt, CANARY_GATES["total_debt"], "Total Debt")
        if error:
            gates_status["failures"].append(error)
            gates_status["gates_passed"] = False
    else:
        gates_status["failures"].append("Balance sheet section missing")
        gates_status["gates_passed"] = False
    
    # Cash flow check
    if "cash_flow" in results:
        cf = results["cash_flow"]
        gates_status["checks_performed"] += 1
        
        actual_cash = float(cf.get("cash_closing", 0) or cf.get("cash_and_equivalents", 0))
        error = check_numeric_tolerance(actual_cash, CANARY_GATES["cash_closing"], "Cash Closing")
        if error:
            gates_status["failures"].append(error)
            gates_status["gates_passed"] = False
    else:
        gates_status["failures"].append("Cash flow section missing")
        gates_status["gates_passed"] = False
    
    # Organization info check
    if "brf_info" in results or "governance" in results:
        org_info = results.get("brf_info", {}) or results.get("governance", {})
        gates_status["checks_performed"] += 1
        
        # Organization number
        org_no = str(org_info.get("organization_number", "") or org_info.get("org_number", ""))
        if CANARY_GATES["org_number"] not in org_no:
            gates_status["failures"].append(f"Org number: expected {CANARY_GATES['org_number']}, got '{org_no}'")
            gates_status["gates_passed"] = False
        
        # Chairman
        chairman = normalize_name(str(org_info.get("chairman", "")))
        expected_chairman = normalize_name(CANARY_GATES["chairman"])
        if expected_chairman not in chairman and chairman not in expected_chairman:
            gates_status["failures"].append(f"Chairman: expected '{CANARY_GATES['chairman']}', got '{org_info.get('chairman', '')}'")
            gates_status["gates_passed"] = False
        
        # Auditor
        auditor = normalize_name(str(org_info.get("auditor_name", "")))
        expected_auditor = normalize_name(CANARY_GATES["auditor_name"])
        if expected_auditor not in auditor and auditor not in expected_auditor:
            gates_status["failures"].append(f"Auditor: expected '{CANARY_GATES['auditor_name']}', got '{org_info.get('auditor_name', '')}'")
            gates_status["gates_passed"] = False
    else:
        gates_status["failures"].append("Organization/governance info missing")
        gates_status["gates_passed"] = False
    
    return gates_status

def test_canary_document() -> int:
    """Test against the actual Sjöstaden 2 document in database"""
    print(f"🎯 Testing Sjöstaden 2 canary document")
    
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cursor = conn.cursor()
        
        # Find Sjöstaden 2 document
        cursor.execute("""
            SELECT id, filename, extraction_data 
            FROM arsredovisning_documents 
            WHERE filename ILIKE '%sjöstad%' AND filename ILIKE '%2024%'
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            print("❌ Sjöstaden 2 (2024) canary document not found")
            return 1
        
        doc_id, filename, extraction_data = row
        print(f"📄 Found canary document: {filename} (id={doc_id})")
        
        if not extraction_data:
            print("❌ No extraction data found for canary document")
            return 1
        
        # Run acceptance gates
        gates = run_acceptance_gates(extraction_data)
        
        print(f"🔍 Performed {gates['checks_performed']} checks")
        
        if gates["gates_passed"]:
            print("✅ All acceptance gates PASSED")
            return 0
        else:
            print("❌ Acceptance gates FAILED:")
            for failure in gates["failures"]:
                print(f"   • {failure}")
            return 1
            
    except Exception as e:
        print(f"❌ Canary test failed: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    parser = argparse.ArgumentParser(description="Run acceptance gate tests")
    parser.add_argument("--canary", choices=["sjostaden_2_2024"], 
                       help="Run canary test against specific document")
    args = parser.parse_args()
    
    if args.canary == "sjostaden_2_2024":
        return test_canary_document()
    else:
        print("No test specified. Use --canary sjostaden_2_2024")
        return 1

if __name__ == "__main__":
    sys.exit(main())