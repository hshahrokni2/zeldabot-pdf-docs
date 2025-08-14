#!/usr/bin/env python3
"""
Integrate Grok supplier research data into the BRF survey system
"""

import json

# Comprehensive supplier database from Grok research
GROK_SUPPLIERS = {
    "cleaning": [
        {
            "name": "Vardagsfrid",
            "phone": "+46 10 516 43 00",
            "email": "info@vardagsfrid.se",
            "address": "Fleminggatan 7, Stockholm",
            "services": "Stairway cleaning, common areas, exteriors, deep cleaning, window cleaning; tailored for property owners and BRFs",
            "pricing_range": "150,000–300,000 SEK/year",
            "rating": 4.5,
            "reviews": "Always delighted, Superb service",
            "sustainability": "Nordic Swan Ecolabel chemical-free products; eco-friendly methods; public transportation for staff",
            "specialties": ["eco-friendly", "nordic-swan-certified", "chemical-free"]
        },
        {
            "name": "Freska",
            "phone": "020-10 00 15",
            "email": "kundtjanst@freska.se", 
            "address": "Årstaängsvägen 17, Stockholm",
            "services": "Regular and deep cleaning of common areas, exteriors, windows; property showing cleaning",
            "pricing_range": "150,000–250,000 SEK/year",
            "rating": 3.5,
            "reviews": "Positive on cleaning quality, complaints on communication",
            "sustainability": "Eco-friendly products; sustainability focus on employee well-being",
            "specialties": ["eco-friendly", "employee-wellbeing"]
        }
    ],
    "heating": [
        {
            "name": "Stockholm Exergi",
            "phone": "020-31 31 51",
            "email": "kundservice@stockholmexergi.se",
            "address": "Jägmästargatan 2, Stockholm",
            "services": "District heating connections, heat pumps, ventilation upgrades; energy efficiency assessments",
            "pricing_range": "500,000–1,000,000 SEK/year",
            "rating": 4.0,
            "reviews": "Positive on sustainability",
            "sustainability": "Highly focused on renewables; bio-CCS for CO2 removal; fossil-free by 2040",
            "specialties": ["renewables", "district-heating", "fossil-free", "bio-ccs"]
        },
        {
            "name": "GK",
            "phone": "+46 8 636 40 00",
            "email": "info@gk.se",
            "address": "Various locations in Stockholm", 
            "services": "HVAC installation, maintenance, ventilation systems; multi-unit buildings",
            "pricing_range": "200,000–400,000 SEK/year",
            "rating": 4.0,
            "reviews": "Generally positive; known for large-scale sustainable projects",
            "sustainability": "Smart, sustainable HVAC; energy-efficient systems",
            "specialties": ["smart-hvac", "energy-efficient", "sustainable-buildings"]
        }
    ],
    "electricity": [
        {
            "name": "Din Elektriker i Stockholm AB",
            "phone": "08-744 11 50",
            "email": "info@dinelektriker.se",
            "address": "Gröndalsvägen 22, Stockholm",
            "services": "Electrical maintenance, LED retrofits, EV charging installations; full BRF services",
            "pricing_range": "100,000–250,000 SEK/year",
            "rating": 4.5,
            "reviews": "Professional, quick",
            "sustainability": "LED retrofits for energy efficiency; EV charging supports sustainable transport",
            "specialties": ["led-retrofit", "ev-charging", "energy-efficiency"]
        },
        {
            "name": "Euro El i Stockholm",
            "phone": "+46 8-644 44 00",
            "email": "contact@euroel.se",
            "address": "Various in Stockholm",
            "services": "Electrical maintenance, retrofits, EV charging; adaptable to BRF needs",
            "pricing_range": "100,000–250,000 SEK/year", 
            "rating": 4.0,
            "reviews": "Positive from reviews",
            "sustainability": "Energy-efficient upgrades like LEDs; sustainable integrations",
            "specialties": ["retrofits", "led-upgrade", "maintenance"]
        }
    ],
    "water": [
        {
            "name": "Cyklande Rörmokaren",
            "phone": "08-30 81 00",
            "email": "hej@cyklanderormokaren.se",
            "address": "Själagårdsgatan 21, Stockholm",
            "services": "Plumbing, water quality testing, leak detection; BRF common areas",
            "pricing_range": "150,000–300,000 SEK/year",
            "rating": 4.5,
            "reviews": "Professional, quick",
            "sustainability": "Eco-friendly (cycling to jobs reduces emissions); sustainable practices",
            "specialties": ["eco-friendly", "cycling-service", "leak-detection"]
        },
        {
            "name": "Alvis Rörakut Service AB",
            "phone": "08-650 01 44",
            "email": "info@alvisrorakut.se",
            "address": "Industrivägen 23, Solna",
            "services": "Plumbing, leak detection, water systems maintenance; BRF-focused",
            "pricing_range": "150,000–300,000 SEK/year",
            "rating": 4.0,
            "reviews": "Quick, professional",
            "sustainability": "Sustainable water management; energy-efficient VVS solutions",
            "specialties": ["water-management", "energy-efficient", "vvs"]
        }
    ],
    "recycling": [
        {
            "name": "Envac",
            "phone": "+46 8 785 00 10",
            "email": "info@envac.se",
            "address": "Fleminggatan 7, Stockholm",
            "services": "Automated waste collection, recycling, composting; designed for BRFs like Hammarby Sjöstad",
            "pricing_range": "200,000–500,000 SEK/year",
            "rating": 4.5,
            "reviews": "Positive in urban sustainability contexts",
            "sustainability": "Reduces emissions by 90%, promotes circular economy, data-driven recycling",
            "specialties": ["automated-collection", "circular-economy", "emission-reduction"]
        },
        {
            "name": "Sortera",
            "phone": "+46 8-409 166 00", 
            "email": "info@sortera.se",
            "address": "Årstaängsvägen 21B, Stockholm",
            "services": "Waste collection, recycling, composting; BRF services",
            "pricing_range": "100,000–250,000 SEK/year",
            "rating": 4.0,
            "reviews": "Positive on environmental impact",
            "sustainability": "Circular economy focus; 100% recycling goal; sustainable waste transformation",
            "specialties": ["circular-economy", "100%-recycling", "composting"]
        }
    ],
    "snow_removal": [
        {
            "name": "SmartaVal AB",
            "phone": "+46 8-722 22 00",
            "email": "info@smarta-val.se",
            "address": "Stockholm",
            "services": "Snow removal, de-icing, pathway clearing; adaptable to BRFs",
            "pricing_range": "50,000–150,000 SEK/year",
            "rating": 4.0,
            "reviews": "Positive; eco-focus noted",
            "sustainability": "Eco-clean services; sustainable methods in maintenance",
            "specialties": ["eco-clean", "sustainable-methods", "de-icing"]
        },
        {
            "name": "Söder OM Söder Kontor & Fastighetsservice AB",
            "phone": "08-572 301 00",
            "email": "info@soderomsoder.se",
            "address": "Konsumentvägen 12, Älvsjö",
            "services": "Winter maintenance, snow removal for BRFs",
            "pricing_range": "50,000–150,000 SEK/year",
            "rating": 4.0,
            "reviews": "Positive on service quality",
            "sustainability": "Miljövänliga metoder; sustainable practices",
            "specialties": ["winter-maintenance", "sustainable-practices"]
        }
    ],
    "gardening": [
        {
            "name": "Urbangreen",
            "phone": "+46 8-634 54 00",
            "email": "info@urbangreen.se",
            "address": "Stockholm",
            "services": "Courtyard maintenance, green roofs, plantings; BRF-focused",
            "pricing_range": "200,000–400,000 SEK/year",
            "rating": 4.5,
            "reviews": "Positive in green urban solutions",
            "sustainability": "Specializes in sustainable rooftop landscapes, green infrastructure",
            "specialties": ["green-roofs", "sustainable-landscapes", "green-infrastructure"]
        },
        {
            "name": "Green Landscaping Group",
            "phone": "+46 8-518 05 000",
            "email": "info@greenlandscaping.com",
            "address": "Biblioteksgatan 25, Stockholm",
            "services": "Landscaping, green roofs, courtyard maintenance for BRFs",
            "pricing_range": "200,000–400,000 SEK/year",
            "rating": 4.0,
            "reviews": "Positive",
            "sustainability": "Sustainable outdoor environments; eco-friendly practices",
            "specialties": ["sustainable-outdoor", "eco-friendly", "landscaping"]
        }
    ],
    "administration": [
        {
            "name": "Fastighetsägarna Service Stockholm AB",
            "phone": "08-617 75 00",
            "email": "service@fastighetsagarna.se", 
            "address": "Alströmergatan 14, Stockholm",
            "services": "Administration, board support, financial services; full BRF management",
            "pricing_range": "300,000–600,000 SEK/year",
            "rating": 3.5,
            "reviews": "Mixed; some positive, some complaints on communication",
            "sustainability": "Sustainable property management practices",
            "specialties": ["full-brf-management", "board-support", "financial-services"]
        },
        {
            "name": "Jakobsen Properties AB",
            "phone": "076-767 09 97",
            "email": "henrik@jproperties.se",
            "address": "Ljusslingan 30 a, Stockholm", 
            "services": "Administration, board support, financial for BRFs; digital tools",
            "pricing_range": "300,000–600,000 SEK/year",
            "rating": 4.0,
            "reviews": "Positive on service",
            "sustainability": "Sustainable fastighetsförvaltning",
            "specialties": ["digital-tools", "sustainable-management", "board-support"]
        }
    ],
    "security": [
        {
            "name": "Svenska Hemlarm",
            "phone": "+46 8-600 55 00",
            "email": "info@svenskahemlarm.se",
            "address": "Primusgatan 18, Stockholm",
            "services": "Access control, cameras, alarms; BRF security",
            "pricing_range": "100,000–300,000 SEK/year",
            "rating": 4.0,
            "reviews": "Positive from reviews",
            "sustainability": "Modern, energy-efficient systems",
            "specialties": ["access-control", "energy-efficient", "modern-systems"]
        },
        {
            "name": "SOS Alarm Sverige AB",
            "phone": "020-31 31 51",
            "email": "info@sosalarm.se",
            "address": "Stockholm",
            "services": "Alarm systems, access control; emergency services for BRFs",
            "pricing_range": "100,000–300,000 SEK/year", 
            "rating": 4.0,
            "reviews": "Positive on reliability",
            "sustainability": "Sustainable operations in emergency response",
            "specialties": ["emergency-services", "reliability", "sustainable-operations"]
        }
    ],
    "insurance": [
        {
            "name": "Folksam",
            "phone": "0771-950 950",
            "email": "info@folksam.se",
            "address": "Bohusgatan 14, Stockholm",
            "services": "BRF property and liability insurance; climate adaptation coverage",
            "pricing_range": "200,000–500,000 SEK/year",
            "rating": 3.5,
            "reviews": "Mixed; positive on claims, complaints on service",
            "sustainability": "Investments in sustainable projects; climate-related bonds",
            "specialties": ["climate-adaptation", "sustainable-investments", "property-liability"]
        },
        {
            "name": "Trygg-Hansa",
            "phone": "0771-111 110", 
            "email": "info@trygghansa.se",
            "address": "Fleminggatan 18, Stockholm",
            "services": "BRF-specific property, liability; additional covers",
            "pricing_range": "200,000–500,000 SEK/year",
            "rating": 3.5,
            "reviews": "Mixed; some positive, complaints on claims",
            "sustainability": "Focus on sustainable living; green initiatives in policies",
            "specialties": ["sustainable-living", "green-initiatives", "additional-covers"]
        }
    ]
}

def update_supplier_database():
    """Update the enhanced survey system with Grok supplier data"""
    
    # Save the comprehensive supplier database
    with open('grok_suppliers_database.json', 'w', encoding='utf-8') as f:
        json.dump(GROK_SUPPLIERS, f, indent=2, ensure_ascii=False)
    
    print("✅ Grok supplier database created!")
    print(f"Total suppliers: {sum(len(suppliers) for suppliers in GROK_SUPPLIERS.values())}")
    
    for category, suppliers in GROK_SUPPLIERS.items():
        print(f"  {category}: {len(suppliers)} suppliers")
        for supplier in suppliers:
            rating_emoji = "⭐" * int(supplier['rating']) + "⚪" * (5 - int(supplier['rating']))
            print(f"    • {supplier['name']} ({rating_emoji} {supplier['rating']}) - {supplier['pricing_range']}")
    
    # Create integration script for the enhanced survey
    integration_code = f"""
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
    return f\"\"\"
    **{{supplier['name']}}** ⭐ {{supplier['rating']}}/5
    📞 {{supplier['phone']}}
    ✉️ {{supplier['email']}}
    📍 {{supplier['address']}}
    
    **Services:** {{supplier['services']}}
    **Pricing:** {{supplier['pricing_range']}}
    **Sustainability:** {{supplier['sustainability']}}
    \"\"\"
"""
    
    with open('supplier_integration_code.py', 'w') as f:
        f.write(integration_code)
    
    return GROK_SUPPLIERS

if __name__ == "__main__":
    update_supplier_database()