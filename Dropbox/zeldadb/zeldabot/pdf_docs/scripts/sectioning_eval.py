#!/usr/bin/env python3
"""
Sectioning Evaluation Script
Compares predicted headers against gold standard with strict requirements
Coverage, Level Accuracy, Page Range Accuracy must all be 100% for --require-perfect
"""

import os
import re
import json
import argparse
import unicodedata
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher

class SectioningEvaluator:
    def __init__(self, require_perfect: bool = False):
        self.require_perfect = require_perfect
        
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison using NFKC"""
        text = unicodedata.normalize('NFKC', text)
        text = ' '.join(text.split())  # Collapse whitespace
        return text.strip().lower()
    
    def extract_headers_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract headers from either format"""
        if "headers" in data:
            # Post-filtered format
            headers = []
            for header in data["headers"]:
                headers.append(header)
                # Add children if present
                if "children" in header:
                    headers.extend(header["children"])
            return headers
        elif "pages" in data:
            # Raw agent format
            headers = []
            for page_data in data["pages"]:
                for header in page_data.get("headers", []):
                    if "page" not in header:
                        header["page"] = page_data.get("page", 0)
                    headers.append(header)
            return headers
        else:
            return []
    
    def find_best_match(self, pred_header: Dict, gold_headers: List[Dict], 
                       used_gold_indices: set) -> Tuple[int, float]:
        """Find best matching gold header for predicted header"""
        pred_text = self.normalize_text(pred_header.get("text", ""))
        
        best_idx = -1
        best_score = 0.0
        
        for i, gold_header in enumerate(gold_headers):
            if i in used_gold_indices:
                continue
                
            gold_text = self.normalize_text(gold_header.get("text", ""))
            
            # Calculate similarity score
            similarity = SequenceMatcher(None, pred_text, gold_text).ratio()
            
            # Exact match bonus
            if pred_text == gold_text:
                similarity = 1.0
                
            if similarity > best_score and similarity >= 0.8:  # Minimum similarity threshold
                best_score = similarity
                best_idx = i
        
        return best_idx, best_score
    
    def evaluate_coverage(self, pred_headers: List[Dict], gold_headers: List[Dict]) -> Dict[str, Any]:
        """Evaluate coverage: how many gold headers were found"""
        
        used_gold_indices = set()
        matches = []
        
        for pred_header in pred_headers:
            best_idx, similarity = self.find_best_match(pred_header, gold_headers, used_gold_indices)
            
            if best_idx >= 0:
                used_gold_indices.add(best_idx)
                matches.append({
                    "predicted": pred_header,
                    "gold": gold_headers[best_idx],
                    "similarity": similarity
                })
        
        coverage = len(matches) / len(gold_headers) if gold_headers else 0.0
        
        # Find missing headers
        missing = []
        for i, gold_header in enumerate(gold_headers):
            if i not in used_gold_indices:
                missing.append(gold_header)
        
        return {
            "coverage": coverage,
            "matched_count": len(matches),
            "gold_count": len(gold_headers),
            "missing_count": len(missing),
            "matches": matches,
            "missing_headers": missing
        }
    
    def evaluate_levels(self, matches: List[Dict]) -> Dict[str, Any]:
        """Evaluate level accuracy for matched headers"""
        
        if not matches:
            return {"level_accuracy": 0.0, "correct_levels": 0, "total_matches": 0}
        
        correct_levels = 0
        level_errors = []
        
        for match in matches:
            pred_level = match["predicted"].get("level")
            gold_level = match["gold"].get("level")
            
            if pred_level == gold_level:
                correct_levels += 1
            else:
                level_errors.append({
                    "text": match["predicted"]["text"],
                    "predicted_level": pred_level,
                    "gold_level": gold_level
                })
        
        level_accuracy = correct_levels / len(matches)
        
        return {
            "level_accuracy": level_accuracy,
            "correct_levels": correct_levels,
            "total_matches": len(matches),
            "level_errors": level_errors
        }
    
    def evaluate_page_ranges(self, matches: List[Dict]) -> Dict[str, Any]:
        """Evaluate page range accuracy for matched headers"""
        
        if not matches:
            return {"page_range_accuracy": 0.0, "correct_ranges": 0, "total_matches": 0}
        
        correct_ranges = 0
        range_errors = []
        
        for match in matches:
            pred = match["predicted"]
            gold = match["gold"]
            
            pred_start = pred.get("page", pred.get("start_page"))
            pred_end = pred.get("end_page", pred_start)  # Default to start page if no end
            
            gold_start = gold.get("page", gold.get("start_page"))
            gold_end = gold.get("end_page", gold_start)  # Default to start page if no end
            
            if pred_start == gold_start and pred_end == gold_end:
                correct_ranges += 1
            else:
                range_errors.append({
                    "text": pred["text"],
                    "predicted_range": f"{pred_start}-{pred_end}",
                    "gold_range": f"{gold_start}-{gold_end}"
                })
        
        page_range_accuracy = correct_ranges / len(matches)
        
        return {
            "page_range_accuracy": page_range_accuracy,
            "correct_ranges": correct_ranges,
            "total_matches": len(matches),
            "range_errors": range_errors
        }
    
    def evaluate(self, pred_data: Dict[str, Any], gold_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main evaluation function"""
        
        print("🔍 Extracting headers from predictions and gold standard...")
        
        pred_headers = self.extract_headers_list(pred_data)
        gold_headers = self.extract_headers_list(gold_data)
        
        print(f"   Predicted headers: {len(pred_headers)}")
        print(f"   Gold headers: {len(gold_headers)}")
        
        if not gold_headers:
            return {"error": "No gold headers found"}
        
        # Evaluate coverage
        print("\\n📊 Evaluating coverage...")
        coverage_result = self.evaluate_coverage(pred_headers, gold_headers)
        print(f"   Coverage: {coverage_result['coverage']:.1%} ({coverage_result['matched_count']}/{coverage_result['gold_count']})")
        
        if coverage_result['missing_count'] > 0:
            print(f"   Missing headers: {coverage_result['missing_count']}")
            for missing in coverage_result['missing_headers'][:3]:  # Show first 3
                print(f"     - '{missing['text']}'")
        
        # Evaluate levels
        print("\\n🎯 Evaluating level accuracy...")
        level_result = self.evaluate_levels(coverage_result['matches'])
        print(f"   Level accuracy: {level_result['level_accuracy']:.1%} ({level_result['correct_levels']}/{level_result['total_matches']})")
        
        if level_result['level_errors']:
            print(f"   Level errors: {len(level_result['level_errors'])}")
            for error in level_result['level_errors'][:3]:  # Show first 3
                print(f"     - '{error['text']}': predicted L{error['predicted_level']}, gold L{error['gold_level']}")
        
        # Evaluate page ranges
        print("\\n📄 Evaluating page range accuracy...")
        range_result = self.evaluate_page_ranges(coverage_result['matches'])
        print(f"   Page range accuracy: {range_result['page_range_accuracy']:.1%} ({range_result['correct_ranges']}/{range_result['total_matches']})")
        
        if range_result['range_errors']:
            print(f"   Range errors: {len(range_result['range_errors'])}")
            for error in range_result['range_errors'][:3]:  # Show first 3
                print(f"     - '{error['text']}': predicted {error['predicted_range']}, gold {error['gold_range']}")
        
        # Overall evaluation
        overall_scores = {
            "coverage": coverage_result['coverage'],
            "level_accuracy": level_result['level_accuracy'], 
            "page_range_accuracy": range_result['page_range_accuracy']
        }
        
        all_perfect = all(score == 1.0 for score in overall_scores.values())
        
        print(f"\\n🎯 OVERALL SCORES:")
        print(f"   Coverage: {overall_scores['coverage']:.1%}")
        print(f"   Level Accuracy: {overall_scores['level_accuracy']:.1%}")
        print(f"   Page Range Accuracy: {overall_scores['page_range_accuracy']:.1%}")
        print(f"   Perfect: {'✅ YES' if all_perfect else '❌ NO'}")
        
        if self.require_perfect and not all_perfect:
            print("\\n❌ FAILURE: --require-perfect specified but scores are not 100%")
            return {
                "success": False,
                "reason": "Perfect scores required but not achieved",
                **overall_scores,
                "coverage_details": coverage_result,
                "level_details": level_result,
                "range_details": range_result
            }
        
        return {
            "success": True,
            **overall_scores,
            "coverage_details": coverage_result,
            "level_details": level_result,
            "range_details": range_result
        }

def main():
    parser = argparse.ArgumentParser(description="Sectioning Evaluation")
    parser.add_argument("--gold", required=True, help="Gold standard JSON file")
    parser.add_argument("--pred", required=True, help="Predicted results JSON file")
    parser.add_argument("--require-perfect", action="store_true", help="Require 100% scores")
    parser.add_argument("--report", required=True, help="Output evaluation report JSON")
    args = parser.parse_args()
    
    # Check input files exist
    if not os.path.exists(args.gold):
        print(f"❌ Gold file not found: {args.gold}")
        return 1
        
    if not os.path.exists(args.pred):
        print(f"❌ Predictions file not found: {args.pred}")
        return 1
    
    # Load data
    print(f"📖 Loading gold standard: {args.gold}")
    with open(args.gold, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    
    print(f"📖 Loading predictions: {args.pred}")  
    with open(args.pred, 'r', encoding='utf-8') as f:
        pred_data = json.load(f)
    
    # Evaluate
    evaluator = SectioningEvaluator(require_perfect=args.require_perfect)
    result = evaluator.evaluate(pred_data, gold_data)
    
    # Save report
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\\n📋 Evaluation report saved to: {args.report}")
    
    if not result.get("success", True):
        print("❌ Evaluation failed")
        return 1
    
    print("✅ Evaluation completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())