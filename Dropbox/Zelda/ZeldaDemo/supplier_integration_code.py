
# Integration code for enhanced survey system
import json

def load_grok_suppliers():
    with open('grok_suppliers_database.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_supplier_alternatives(category, current_rating):
    suppliers = load_grok_suppliers()
    if category in suppliers:
        # Return suppliers with rating > current_rating
        alternatives = [s for s in suppliers[category] if s['rating'] > current_rating]
        return sorted(alternatives, key=lambda x: x['rating'], reverse=True)[:3]
    return []

def format_supplier_recommendation(supplier):
    return f"""
    **{supplier['name']}** ⭐ {supplier['rating']}/5
    📞 {supplier['phone']}
    ✉️ {supplier['email']}
    📍 {supplier['address']}
    
    **Services:** {supplier['services']}
    **Pricing:** {supplier['pricing_range']}
    **Sustainability:** {supplier['sustainability']}
    """
