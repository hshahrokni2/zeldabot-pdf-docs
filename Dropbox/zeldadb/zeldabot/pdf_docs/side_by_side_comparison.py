#!/usr/bin/env python3
"""
Side-by-Side Hierarchical Header Comparison
"""
import json

def main():
    # Load the comparison data
    with open("/tmp/hierarchical_comparison.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    qwen_hierarchy = data["qwen_hierarchy"]
    claude_hierarchy = data["claude_hierarchy"]

    print("🔍 SIDE-BY-SIDE HIERARCHICAL COMPARISON")
    print("=" * 80)
    print(f"{'QWEN 2.5-VL STRUCTURE':^40} | {'CLAUDE STRUCTURE':^37}")
    print("=" * 40 + "|" + "=" * 39)

    # Create display lists
    qwen_display = []
    claude_display = []

    def add_to_display(hierarchy, display_list):
        for main_header in hierarchy:
            pages = f"({main_header['start_page']}-{main_header['end_page']})"
            display_list.append(f"📌 {main_header['header']} {pages}")
            
            for sub in main_header["subheaders"]:
                sub_pages = f"({sub['start_page']}-{sub['end_page']})"
                display_list.append(f"   ├─ {sub['header']} {sub_pages}")
                
                for subsub in sub.get("subheaders", []):
                    subsub_pages = f"({subsub['start_page']}-{subsub['end_page']})"
                    display_list.append(f"      └─ {subsub['header']} {subsub_pages}")

    add_to_display(qwen_hierarchy, qwen_display)
    add_to_display(claude_hierarchy, claude_display)

    # Pad shorter list
    max_lines = max(len(qwen_display), len(claude_display))
    while len(qwen_display) < max_lines:
        qwen_display.append("")
    while len(claude_display) < max_lines:
        claude_display.append("")

    # Print side by side with proper truncation
    for i in range(max_lines):
        qwen_line = qwen_display[i]
        claude_line = claude_display[i]
        
        # Truncate if too long
        if len(qwen_line) > 38:
            qwen_line = qwen_line[:35] + "..."
        if len(claude_line) > 37:
            claude_line = claude_line[:34] + "..."
        
        print(f"{qwen_line:<40} | {claude_line:<37}")

    print("=" * 40 + "|" + "=" * 39)
    print(f"{'SUMMARY:':^40} | {'SUMMARY:':^37}")
    
    qwen_main = len(qwen_hierarchy)
    claude_main = len(claude_hierarchy)
    qwen_subs = sum(len(h["subheaders"]) for h in qwen_hierarchy)
    claude_subs = sum(len(h["subheaders"]) for h in claude_hierarchy)
    
    print(f"Main headers: {qwen_main:>28} | Main headers: {claude_main:>25}")
    print(f"Subheaders: {qwen_subs:>30} | Subheaders: {claude_subs:>27}")
    print("=" * 80)
    
    # Key differences
    print("\n🎯 KEY STRUCTURAL DIFFERENCES:")
    print("-" * 50)
    print("QWEN: Hierarchical (7 main + 23 sub)")
    print("  ✅ NOTER contains individual notes as subheaders")
    print("  ✅ Proper parent-child relationships")
    print("  ❌ Some missing detailed subsections")
    
    print("\nCLAUDE: Flat (25 main + 6 sub)")
    print("  ❌ Individual notes as independent main headers")
    print("  ❌ Loses hierarchical document structure")
    print("  ✅ More granular detail in Balance Sheet")
    print("  ✅ Better end-page detection")

if __name__ == "__main__":
    main()