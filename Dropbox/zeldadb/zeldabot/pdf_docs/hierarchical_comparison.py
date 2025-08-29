#!/usr/bin/env python3
"""
Hierarchical Header Comparison - Qwen vs Claude
Creates nested JSON structure showing main headers with their subheaders
"""
import json

# Qwen's extraction results (from previous H100 run)
qwen_headers = [
    {'header': 'FÖRVALTNINGSBERÄTTELSE', 'level': 1, 'start_page': 2, 'end_page': 2},
    {'header': 'Verksamheten', 'level': 2, 'start_page': 3, 'end_page': 3},
    {'header': 'Väsentliga händelser under räkenskapsåret', 'level': 3, 'start_page': 3, 'end_page': 3},
    {'header': 'Väsentliga händelser efter räkenskapsårets utgång', 'level': 3, 'start_page': 3, 'end_page': 3},
    {'header': 'Förväntad framtida utveckling', 'level': 3, 'start_page': 3, 'end_page': 3},
    {'header': 'RESULTATRÄKNING', 'level': 1, 'start_page': 4, 'end_page': 4},
    {'header': 'BALANSRÄKNING', 'level': 1, 'start_page': 5, 'end_page': 5},
    {'header': 'TILLGÅNGAR', 'level': 2, 'start_page': 5, 'end_page': 5},
    {'header': 'Anläggningstillgångar', 'level': 3, 'start_page': 5, 'end_page': 5},
    {'header': 'Omsättningstillgångar', 'level': 3, 'start_page': 5, 'end_page': 5},
    {'header': 'EGET KAPITAL OCH SKULDER', 'level': 2, 'start_page': 6, 'end_page': 6},
    {'header': 'Eget kapital', 'level': 3, 'start_page': 6, 'end_page': 6},
    {'header': 'Skulder', 'level': 3, 'start_page': 6, 'end_page': 6},
    {'header': 'KASSAFLÖDESANALYS', 'level': 1, 'start_page': 7, 'end_page': 7},
    {'header': 'Kassaflöde från den löpande verksamheten', 'level': 2, 'start_page': 7, 'end_page': 7},
    {'header': 'Kassaflöde från investeringsverksamheten', 'level': 2, 'start_page': 7, 'end_page': 7},
    {'header': 'NOTER', 'level': 1, 'start_page': 8, 'end_page': 8},
    {'header': 'Not 1 Allmänna redovisningsprinciper', 'level': 3, 'start_page': 9, 'end_page': 9},
    {'header': 'Not 2 Intäkter', 'level': 3, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 3 Drift- och underhållskostnader', 'level': 3, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 4 Fastighetsskatt och avgifter', 'level': 3, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 5 Administrationskostnader', 'level': 3, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 6 Av- och nedskrivningar', 'level': 3, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 7 Ränteintäkter och liknande resultatposter', 'level': 3, 'start_page': 12, 'end_page': 12},
    {'header': 'Not 8 Räntekostnader och liknande resultatposter', 'level': 3, 'start_page': 12, 'end_page': 12},
    {'header': 'Not 9 Byggnader och mark', 'level': 3, 'start_page': 12, 'end_page': 12},
    {'header': 'Not 10 Maskiner och inventarier', 'level': 3, 'start_page': 12, 'end_page': 12},
    {'header': 'Not 11 Kortfristiga fordringar', 'level': 3, 'start_page': 13, 'end_page': 13},
    {'header': 'Not 12 Förutbetalda kostnader och upplupna intäkter', 'level': 3, 'start_page': 13, 'end_page': 13},
    {'header': 'Not 13 Kassa och bank', 'level': 3, 'start_page': 13, 'end_page': 13},
    {'header': 'Not 14 Eget kapital', 'level': 3, 'start_page': 13, 'end_page': 13},
    {'header': 'Not 15 Avsättningar', 'level': 3, 'start_page': 14, 'end_page': 14},
    {'header': 'Not 16 Långfristiga skulder', 'level': 3, 'start_page': 14, 'end_page': 14},
    {'header': 'Not 17 Kortfristiga skulder', 'level': 3, 'start_page': 14, 'end_page': 14},
    {'header': 'Not 18 Upplupna kostnader och förutbetalda intäkter', 'level': 3, 'start_page': 15, 'end_page': 15},
    {'header': 'STYRELSE', 'level': 1, 'start_page': 16, 'end_page': 16},
    {'header': 'REVISIONSBERÄTTELSE', 'level': 1, 'start_page': 17, 'end_page': 17}
]

# Claude's manual extraction
claude_headers = [
    {'header': 'FÖRVALTNINGSBERÄTTELSE', 'level': 1, 'start_page': 2, 'end_page': 3},
    {'header': 'Verksamheten', 'level': 2, 'start_page': 3, 'end_page': 3},
    {'header': 'Väsentliga händelser under räkenskapsåret', 'level': 3, 'start_page': 3, 'end_page': 3},
    {'header': 'Väsentliga händelser efter räkenskapsårets utgång', 'level': 3, 'start_page': 3, 'end_page': 3},
    {'header': 'Förväntad framtida utveckling', 'level': 3, 'start_page': 3, 'end_page': 3},
    {'header': 'RESULTATRÄKNING', 'level': 1, 'start_page': 4, 'end_page': 4},
    {'header': 'BALANSRÄKNING', 'level': 1, 'start_page': 5, 'end_page': 6},
    {'header': 'TILLGÅNGAR', 'level': 2, 'start_page': 5, 'end_page': 5},
    {'header': 'Anläggningstillgångar', 'level': 3, 'start_page': 5, 'end_page': 5},
    {'header': 'Materiella anläggningstillgångar', 'level': 4, 'start_page': 5, 'end_page': 5},
    {'header': 'Omsättningstillgångar', 'level': 3, 'start_page': 5, 'end_page': 5},
    {'header': 'Kortfristiga fordringar', 'level': 4, 'start_page': 5, 'end_page': 5},
    {'header': 'Kassa och bank', 'level': 4, 'start_page': 5, 'end_page': 5},
    {'header': 'EGET KAPITAL OCH SKULDER', 'level': 2, 'start_page': 6, 'end_page': 6},
    {'header': 'Eget kapital', 'level': 3, 'start_page': 6, 'end_page': 6},
    {'header': 'Skulder', 'level': 3, 'start_page': 6, 'end_page': 6},
    {'header': 'Långfristiga skulder', 'level': 4, 'start_page': 6, 'end_page': 6},
    {'header': 'Kortfristiga skulder', 'level': 4, 'start_page': 6, 'end_page': 6},
    {'header': 'KASSAFLÖDESANALYS', 'level': 1, 'start_page': 7, 'end_page': 7},
    {'header': 'Kassaflöde från den löpande verksamheten', 'level': 2, 'start_page': 7, 'end_page': 7},
    {'header': 'Kassaflöde från investeringsverksamheten', 'level': 2, 'start_page': 7, 'end_page': 7},
    {'header': 'Kassaflöde från finansieringsverksamheten', 'level': 2, 'start_page': 7, 'end_page': 7},
    {'header': 'NOTER', 'level': 1, 'start_page': 8, 'end_page': 15},
    {'header': 'Not 1 Allmänna redovisningsprinciper', 'level': 1, 'start_page': 9, 'end_page': 10},
    {'header': 'Not 2 Intäkter', 'level': 1, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 3 Drift- och underhållskostnader', 'level': 1, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 4 Fastighetsskatt och avgifter', 'level': 1, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 5 Administrationskostnader', 'level': 1, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 6 Av- och nedskrivningar', 'level': 1, 'start_page': 11, 'end_page': 11},
    {'header': 'Not 7 Ränteintäkter och liknande resultatposter', 'level': 1, 'start_page': 12, 'end_page': 12},
    {'header': 'Not 8 Räntekostnader och liknande resultatposter', 'level': 1, 'start_page': 12, 'end_page': 12},
    {'header': 'Not 9 Byggnader och mark', 'level': 1, 'start_page': 12, 'end_page': 12},
    {'header': 'Not 10 Maskiner och inventarier', 'level': 1, 'start_page': 12, 'end_page': 12},
    {'header': 'Not 11 Kortfristiga fordringar', 'level': 1, 'start_page': 13, 'end_page': 13},
    {'header': 'Not 12 Förutbetalda kostnader och upplupna intäkter', 'level': 1, 'start_page': 13, 'end_page': 13},
    {'header': 'Not 13 Kassa och bank', 'level': 1, 'start_page': 13, 'end_page': 13},
    {'header': 'Not 14 Eget kapital', 'level': 1, 'start_page': 13, 'end_page': 13},
    {'header': 'Not 15 Avsättningar', 'level': 1, 'start_page': 14, 'end_page': 14},
    {'header': 'Not 16 Långfristiga skulder', 'level': 1, 'start_page': 14, 'end_page': 14},
    {'header': 'Not 17 Kortfristiga skulder', 'level': 1, 'start_page': 14, 'end_page': 14},
    {'header': 'Not 18 Upplupna kostnader och förutbetalda intäkter', 'level': 1, 'start_page': 15, 'end_page': 15},
    {'header': 'STYRELSE', 'level': 1, 'start_page': 16, 'end_page': 16},
    {'header': 'REVISIONSBERÄTTELSE', 'level': 1, 'start_page': 17, 'end_page': 26}
]

def create_hierarchical_structure(headers):
    """Convert flat header list to hierarchical structure"""
    hierarchy = []
    current_parents = {}  # Track current parent at each level
    
    for header in headers:
        level = header['level']
        entry = {
            'header': header['header'],
            'start_page': header['start_page'],
            'end_page': header['end_page'],
            'level': level,
            'subheaders': []
        }
        
        if level == 1:
            # Top level - add to root
            hierarchy.append(entry)
            current_parents = {1: entry}  # Reset parent tracking
        else:
            # Find appropriate parent (go up levels until we find one)
            parent_level = level - 1
            while parent_level >= 1 and parent_level not in current_parents:
                parent_level -= 1
            
            if parent_level >= 1 and parent_level in current_parents:
                current_parents[parent_level]['subheaders'].append(entry)
                current_parents[level] = entry
            else:
                # Fallback: add to root if no parent found
                hierarchy.append(entry)
                current_parents[level] = entry
    
    return hierarchy

def print_hierarchy(hierarchy, title):
    """Print hierarchical structure in readable format"""
    print(f"\n📋 {title}")
    print("=" * 60)
    
    for main_header in hierarchy:
        print(f"📌 {main_header['header']} (pages {main_header['start_page']}-{main_header['end_page']})")
        
        for sub in main_header['subheaders']:
            print(f"   ├─ {sub['header']} (pages {sub['start_page']}-{sub['end_page']})")
            
            for subsub in sub['subheaders']:
                print(f"      └─ {subsub['header']} (pages {subsub['start_page']}-{subsub['end_page']})")

def main():
    """Main comparison function"""
    print("🔍 HIERARCHICAL HEADER COMPARISON - QWEN vs CLAUDE")
    print("=" * 70)
    
    # Create hierarchical structures
    qwen_hierarchy = create_hierarchical_structure(qwen_headers)
    claude_hierarchy = create_hierarchical_structure(claude_headers)
    
    # Print both hierarchies
    print_hierarchy(qwen_hierarchy, "QWEN HIERARCHICAL STRUCTURE")
    print_hierarchy(claude_hierarchy, "CLAUDE HIERARCHICAL STRUCTURE")
    
    # Analysis
    print(f"\n📊 COMPARISON SUMMARY:")
    print("=" * 40)
    
    qwen_main_count = len(qwen_hierarchy)
    claude_main_count = len(claude_hierarchy)
    
    qwen_sub_count = sum(len(h['subheaders']) for h in qwen_hierarchy)
    claude_sub_count = sum(len(h['subheaders']) for h in claude_hierarchy)
    
    print(f"Main headers (Level 1):")
    print(f"  Qwen: {qwen_main_count}")
    print(f"  Claude: {claude_main_count}")
    
    print(f"\nSubheaders (Level 2+):")
    print(f"  Qwen: {qwen_sub_count}")
    print(f"  Claude: {claude_sub_count}")
    
    # Key structural differences
    print(f"\n🔍 KEY STRUCTURAL DIFFERENCES:")
    print("-" * 30)
    
    # Noter section analysis
    qwen_noter = next((h for h in qwen_hierarchy if h['header'] == 'NOTER'), None)
    claude_noter = next((h for h in claude_hierarchy if h['header'] == 'NOTER'), None)
    
    if qwen_noter and claude_noter:
        print(f"NOTER section:")
        print(f"  Qwen: {len(qwen_noter['subheaders'])} subheaders")
        print(f"  Claude: {len(claude_noter['subheaders'])} subheaders")
    
    # Individual Notes classification
    qwen_individual_notes = [h for h in qwen_headers if h['header'].startswith('Not ')]
    claude_individual_notes = [h for h in claude_headers if h['header'].startswith('Not ')]
    
    qwen_note_levels = set(h['level'] for h in qwen_individual_notes)
    claude_note_levels = set(h['level'] for h in claude_individual_notes)
    
    print(f"\nIndividual Note headers (Not 1, Not 2, etc.):")
    print(f"  Qwen classifies as: Level {list(qwen_note_levels)}")
    print(f"  Claude classifies as: Level {list(claude_note_levels)}")
    
    # Missing headers
    qwen_header_names = set(h['header'] for h in qwen_headers)
    claude_header_names = set(h['header'] for h in claude_headers)
    
    qwen_only = qwen_header_names - claude_header_names
    claude_only = claude_header_names - qwen_header_names
    
    if qwen_only:
        print(f"\nHeaders found only by Qwen:")
        for h in qwen_only:
            print(f"  - {h}")
    
    if claude_only:
        print(f"\nHeaders found only by Claude:")
        for h in claude_only:
            print(f"  - {h}")
    
    print(f"\n✅ Hierarchical comparison complete")
    
    # Save JSON output
    output = {
        "qwen_hierarchy": qwen_hierarchy,
        "claude_hierarchy": claude_hierarchy,
        "comparison": {
            "qwen_main_headers": qwen_main_count,
            "claude_main_headers": claude_main_count,
            "qwen_subheaders": qwen_sub_count,
            "claude_subheaders": claude_sub_count
        }
    }
    
    print(f"\n💾 Saving complete comparison as JSON...")
    with open('/tmp/hierarchical_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"   Saved to: /tmp/hierarchical_comparison.json")

if __name__ == "__main__":
    main()