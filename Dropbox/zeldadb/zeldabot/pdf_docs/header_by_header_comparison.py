#!/usr/bin/env python3
"""
Header-by-Header Comparison - Show each header side by side with level and page info
"""
import json

def main():
    # Load the comparison data
    with open("/tmp/hierarchical_comparison.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Get flat lists of all headers
    qwen_flat = []
    claude_flat = []
    
    def flatten_hierarchy(hierarchy, flat_list):
        for main in hierarchy:
            flat_list.append({
                'header': main['header'],
                'level': main['level'],
                'start_page': main['start_page'],
                'end_page': main['end_page']
            })
            for sub in main.get('subheaders', []):
                flat_list.append({
                    'header': sub['header'],
                    'level': sub['level'],
                    'start_page': sub['start_page'],
                    'end_page': sub['end_page']
                })
                for subsub in sub.get('subheaders', []):
                    flat_list.append({
                        'header': subsub['header'],
                        'level': subsub['level'],
                        'start_page': subsub['start_page'],
                        'end_page': subsub['end_page']
                    })
    
    # Also add from original flat data
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
    
    print("📋 HEADER-BY-HEADER DETAILED COMPARISON")
    print("=" * 100)
    print(f"{'QWEN 2.5-VL':^50} | {'CLAUDE':^47}")
    print(f"{'Header (Level) [Pages]':^50} | {'Header (Level) [Pages]':^47}")
    print("=" * 50 + "|" + "=" * 49)
    
    # Create comprehensive comparison by header name
    all_header_names = set()
    qwen_dict = {}
    claude_dict = {}
    
    # Build dictionaries
    for h in qwen_headers:
        header_name = h['header']
        all_header_names.add(header_name)
        qwen_dict[header_name] = h
    
    for h in claude_headers:
        header_name = h['header']
        all_header_names.add(header_name)
        claude_dict[header_name] = h
    
    # Sort headers by page order (using Qwen's page order as base)
    def get_sort_key(header_name):
        if header_name in qwen_dict:
            return qwen_dict[header_name]['start_page']
        elif header_name in claude_dict:
            return claude_dict[header_name]['start_page']
        return 999
    
    sorted_headers = sorted(all_header_names, key=get_sort_key)
    
    # Print each header comparison
    for header_name in sorted_headers:
        qwen_info = qwen_dict.get(header_name)
        claude_info = claude_dict.get(header_name)
        
        # Format Qwen info
        if qwen_info:
            qwen_level = qwen_info['level']
            qwen_pages = f"{qwen_info['start_page']}-{qwen_info['end_page']}"
            qwen_display = f"{header_name} (L{qwen_level}) [{qwen_pages}]"
        else:
            qwen_display = "--- MISSING ---"
        
        # Format Claude info
        if claude_info:
            claude_level = claude_info['level']
            claude_pages = f"{claude_info['start_page']}-{claude_info['end_page']}"
            claude_display = f"{header_name} (L{claude_level}) [{claude_pages}]"
        else:
            claude_display = "--- MISSING ---"
        
        # Truncate if too long
        if len(qwen_display) > 48:
            qwen_display = qwen_display[:45] + "..."
        if len(claude_display) > 45:
            claude_display = claude_display[:42] + "..."
        
        # Add status indicators for differences
        status = ""
        if qwen_info and claude_info:
            if qwen_info['level'] != claude_info['level']:
                status = " 🔄"  # Level difference
            elif (qwen_info['start_page'] != claude_info['start_page'] or 
                  qwen_info['end_page'] != claude_info['end_page']):
                status = " 📄"  # Page difference
            else:
                status = " ✅"  # Match
        elif qwen_info:
            status = " ❌C"  # Missing in Claude
        else:
            status = " ❌Q"  # Missing in Qwen
        
        print(f"{qwen_display:<50} | {claude_display:<45}{status}")
    
    print("=" * 50 + "|" + "=" * 49)
    
    # Summary statistics
    total_headers = len(sorted_headers)
    qwen_count = len(qwen_headers)
    claude_count = len(claude_headers)
    
    both_found = len([h for h in sorted_headers if h in qwen_dict and h in claude_dict])
    qwen_only = len([h for h in sorted_headers if h in qwen_dict and h not in claude_dict])
    claude_only = len([h for h in sorted_headers if h not in qwen_dict and h in claude_dict])
    
    level_matches = sum(1 for h in sorted_headers 
                       if h in qwen_dict and h in claude_dict and 
                       qwen_dict[h]['level'] == claude_dict[h]['level'])
    
    page_matches = sum(1 for h in sorted_headers 
                      if h in qwen_dict and h in claude_dict and 
                      qwen_dict[h]['start_page'] == claude_dict[h]['start_page'] and
                      qwen_dict[h]['end_page'] == claude_dict[h]['end_page'])
    
    print(f"\n📊 DETAILED STATISTICS:")
    print(f"Total unique headers: {total_headers}")
    print(f"Found by both: {both_found}")
    print(f"Qwen only: {qwen_only}")  
    print(f"Claude only: {claude_only}")
    print(f"Level matches: {level_matches}/{both_found} ({level_matches/both_found*100:.1f}%)")
    print(f"Page matches: {page_matches}/{both_found} ({page_matches/both_found*100:.1f}%)")
    
    print(f"\n🎯 LEGEND:")
    print(f"✅ = Perfect match (level + pages)")
    print(f"🔄 = Level difference")
    print(f"📄 = Page range difference")
    print(f"❌Q = Missing in Qwen")
    print(f"❌C = Missing in Claude")

if __name__ == "__main__":
    main()