#!/usr/bin/env python3
"""
Deterministic Header Post-filter + Leveling
- Regex rejects for noise/tables
- Merge near-duplicates 
- "Noter" as L1, "Not X" as L2 children under Noter
"""

import os
import re
import json
import argparse
import unicodedata
from typing import List, Dict, Any, Set
from collections import defaultdict

class HeaderPostFilter:
    def __init__(self):
        # Rejection patterns
        self.reject_patterns = [
            r'^\d+$',  # Pure numbers
            r'^\d{4}-\d{2}-\d{2}$',  # Dates
            r'^\d+\s*kr$',  # Money amounts
            r'^\d+\s*SEK$',  # Money amounts
            r'^\d{6,}-\d{4,}$',  # Org numbers
            r'^sid\s+\d+$',  # Page numbers
            r'^sida\s+\d+$',  # Page numbers
            r'^totalt?$',  # Table totals
            r'^summa$',  # Table sums
            r'^%$',  # Percentage symbols
            r'^x+$',  # Placeholder marks
        ]
        
        # Table indicators (likely in tables, not headers)
        self.table_indicators = [
            r'\d+\s*kr\s*\d+\s*kr',  # Money columns
            r'\d{4}\s+\d{4}',  # Year columns
            r'^\d+\.\d+$',  # Decimal numbers
            r'^\(\d+\)$',  # Parenthetical numbers
        ]
        
        # Common header patterns (boost confidence)
        self.header_boost_patterns = [
            r'årsredovisning',
            r'förvaltningsberättelse',
            r'resultaträkning',
            r'balansräkning',
            r'noter?',
            r'revisionsberättelse',
            r'flerårsöversikt',
            r'kassaflöde',
            r'föreningens?\s+ekonomi',
            r'teknisk\s+status',
            r'fastighetsfakta',
        ]
        
    def normalize_text(self, text: str) -> str:
        """Normalize Swedish text for comparison"""
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        # Collapse whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def should_reject(self, header: Dict[str, Any]) -> bool:
        """Check if header should be rejected"""
        text = header.get("text", "").strip().lower()
        
        if not text:
            return True
            
        # Check rejection patterns
        for pattern in self.reject_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        # Check table indicators
        for pattern in self.table_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        # Reject very short headers (likely noise)
        if len(text) < 3:
            return True
            
        return False
    
    def boost_header_confidence(self, header: Dict[str, Any]) -> Dict[str, Any]:
        """Boost confidence for known Swedish BRF headers"""
        text = header.get("text", "").strip().lower()
        
        confidence_boost = 0
        for pattern in self.header_boost_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                confidence_boost = 0.3
                break
        
        # Add confidence if not present
        if "confidence" not in header:
            header["confidence"] = 0.5 + confidence_boost
        else:
            header["confidence"] = min(1.0, header["confidence"] + confidence_boost)
            
        return header
    
    def merge_near_duplicates(self, headers: List[Dict[str, Any]], 
                            similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Merge headers that are very similar (OCR variants)"""
        from difflib import SequenceMatcher
        
        merged = []
        used_indices: Set[int] = set()
        
        for i, header in enumerate(headers):
            if i in used_indices:
                continue
                
            # Find similar headers
            similar_group = [header]
            used_indices.add(i)
            
            for j, other_header in enumerate(headers[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                text1 = self.normalize_text(header["text"])
                text2 = self.normalize_text(other_header["text"])
                
                similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
                
                if similarity >= similarity_threshold:
                    similar_group.append(other_header)
                    used_indices.add(j)
            
            # Merge group - keep longest text, earliest page
            if len(similar_group) > 1:
                # Sort by text length (desc) then by page (asc)
                similar_group.sort(key=lambda h: (-len(h["text"]), h.get("page", 999)))
                
                merged_header = similar_group[0].copy()
                merged_header["merged_from"] = len(similar_group)
                merged.append(merged_header)
            else:
                merged.append(header)
                
        return merged
    
    def create_hierarchical_structure(self, headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create hierarchical structure with Noter as L1 and 'Not X' as L2 children"""
        
        # First pass: identify Noter sections and their children
        noter_sections = []
        note_items = []
        other_headers = []
        
        for header in headers:
            text = self.normalize_text(header["text"])
            text_lower = text.lower()
            
            # Check if it's "Noter" (Level 1)
            if re.search(r'^noter?$', text_lower):
                header["level"] = 1
                header["header_type"] = "noter_section"
                noter_sections.append(header)
            
            # Check if it's individual note "Not X ..." (Level 2)
            elif re.match(r'^not\s+\d+', text_lower):
                header["level"] = 2
                header["header_type"] = "note_item"
                note_items.append(header)
            
            else:
                # Other headers - preserve original level or assign based on context
                if "level" not in header:
                    # Assign level based on common Swedish BRF sections
                    if any(pattern in text_lower for pattern in [
                        'årsredovisning', 'förvaltningsberättelse', 'resultaträkning', 
                        'balansräkning', 'revisionsberättelse', 'kassaflöde'
                    ]):
                        header["level"] = 1
                    else:
                        header["level"] = 2
                        
                other_headers.append(header)
        
        # Second pass: attach note items to their Noter sections
        structured_headers = []
        
        for header in other_headers + noter_sections:
            if header.get("header_type") == "noter_section":
                # Find note items that belong to this Noter section
                page = header.get("page", 0)
                
                # Find notes on same page or following pages
                children = []
                for note in note_items:
                    note_page = note.get("page", 0)
                    if note_page >= page:
                        children.append(note)
                
                # Sort children by page then by note number
                def extract_note_number(note_text):
                    match = re.search(r'not\s+(\d+)', note_text.lower())
                    return int(match.group(1)) if match else 999
                
                children.sort(key=lambda n: (n.get("page", 0), extract_note_number(n["text"])))
                
                if children:
                    header["children"] = children
                    
            structured_headers.append(header)
        
        # Sort by page number
        structured_headers.sort(key=lambda h: h.get("page", 0))
        
        return structured_headers
    
    def process(self, raw_headers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Main processing pipeline"""
        
        print(f"🔍 Post-filtering {len(raw_headers)} raw headers...")
        
        # Step 1: Reject noise
        valid_headers = []
        rejected_count = 0
        
        for header in raw_headers:
            if self.should_reject(header):
                rejected_count += 1
                continue
                
            # Normalize text
            header["text"] = self.normalize_text(header["text"])
            
            # Boost confidence for known patterns
            header = self.boost_header_confidence(header)
            
            valid_headers.append(header)
        
        print(f"   ✅ Kept {len(valid_headers)} headers, rejected {rejected_count}")
        
        # Step 2: Merge near-duplicates
        merged_headers = self.merge_near_duplicates(valid_headers)
        merge_count = len(valid_headers) - len(merged_headers)
        
        if merge_count > 0:
            print(f"   🔗 Merged {merge_count} near-duplicates")
        
        # Step 3: Create hierarchical structure
        structured_headers = self.create_hierarchical_structure(merged_headers)
        
        # Count hierarchical stats
        level_counts = defaultdict(int)
        children_count = 0
        
        for header in structured_headers:
            level_counts[header.get("level", "unknown")] += 1
            if "children" in header:
                children_count += len(header["children"])
        
        print(f"   📊 Levels: {dict(level_counts)}")
        print(f"   👶 Children: {children_count}")
        
        return {
            "headers": structured_headers,
            "stats": {
                "raw_count": len(raw_headers),
                "valid_count": len(valid_headers),
                "rejected_count": rejected_count,
                "merged_count": merge_count,
                "final_count": len(structured_headers),
                "children_count": children_count,
                "level_distribution": dict(level_counts)
            }
        }

def main():
    parser = argparse.ArgumentParser(description="Header Post-filter")
    parser.add_argument("--in", dest="input_path", required=True, help="Input raw JSON")
    parser.add_argument("--out", required=True, help="Output clean JSON")
    args = parser.parse_args()
    
    if not os.path.exists(args.input_path):
        print(f"❌ Input file not found: {args.input_path}")
        return 1
    
    # Load raw headers
    with open(args.input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Collect all headers from all pages
    all_headers = []
    for page_data in data.get("pages", []):
        headers = page_data.get("headers", [])
        for header in headers:
            # Ensure page number is set
            if "page" not in header:
                header["page"] = page_data.get("page", 0)
            all_headers.append(header)
    
    # Process headers
    filter_processor = HeaderPostFilter()
    result = filter_processor.process(all_headers)
    
    # Save cleaned result
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cleaned headers saved to {args.out}")
    return 0

if __name__ == "__main__":
    exit(main())