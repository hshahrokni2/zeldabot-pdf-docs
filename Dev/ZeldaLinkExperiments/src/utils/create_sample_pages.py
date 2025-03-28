#!/usr/bin/env python3
"""
Create sample OCR pages for testing LLM extraction

This script creates sample OCR pages from Swedish housing association
annual reports to test different LLM models' extraction capabilities.
"""

import os
import json
from datetime import datetime
from pathlib import Path

def ensure_dir(directory):
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def create_tradgarden_samples():
    """Create sample pages for Tradgarden BRF."""
    ocr_dir = Path("./experiments/mistral_ocr_results")
    ensure_dir(ocr_dir)
    
    # Create Tradgarden sample (board members page)
    tradgarden_ocr = {
        "document_id": "tradgarden_samples",
        "pages": [
            {
                "page_num": 1,
                "text": "BRF TRÄDGÅRDEN 1 GUSTAVSBERG\nORGANISATIONSNUMMER: 769636-3808\nÅRSREDOVISNING 2023\n\nBostadsrättsföreningen Trädgården 1 Gustavsberg\nAdress: Gustavsbergsvägen 12, 134 41 Gustavsberg\nTfn: 08-123 45 67\nE-post: info@brftradgarden1.se\nHemsida: www.brftradgarden1.se\n\nFastighetsbeteckning: Gustavsberg 1:71\nTotal yta: 3 246 kvm\nBostadsyta (BOA): 2 980 kvm\nLokalyta (LOA): 266 kvm"
            },
            {
                "page_num": 2, 
                "text": "STYRELSE OCH FUNKTIONÄRER\n\nStylelseledamöter\nOrdinarie ledamöter\nAnna Andersson\t\tOrdförande\nBengt Bengtsson\t\tSekreterare\nCarl Carlsson\t\tKassör\nDiana Danielsson\tLedamot\nErik Eriksson\t\tLedamot\n\nSuppleanter\nFredrik Fredriksson\t\tSuppleant\nGunilla Gustafsson\tSuppleant\n\nRevisorer\nHans Hansson\t\tOrdinarie revisor, extern, EY\nInga Ivarsson\t\tRevisorssuppleant, extern, EY\n\nValberedning\nJohan Johansson\t\tSammankallande\nKarin Karlsson\t\tLedamot"
            },
            {
                "page_num": 3,
                "text": "FÖRVALTNINGSBERÄTTELSE\n\nVerksamheten\nFöreningen har till ändamål att främja medlemmarnas ekonomiska intressen genom att i föreningens hus upplåta bostadslägenheter och lokaler under nyttjanderätt och utan tidsbegränsning. Föreningen bildades 2018-06-10 och förvärvade fastigheten Gustavsberg 1:71 genom köp samma år. Byggnationen påbörjades under hösten 2018 och slutfördes under 2020."
            },
            {
                "page_num": 4,
                "text": "RESULTATRÄKNING\n\nRörelsens intäkter\t\t\t\t2023\t\t\t2022\nÅrsavgifter\t\t\t\t\t3 471 600\t\t3 471 600\nHyresintäkter lokaler\t\t\t264 000\t\t\t264 000\nÖvriga intäkter\t\t\t\t52 400\t\t\t48 300\nSumma rörelsens intäkter\t\t3 788 000\t\t3 783 900\n\nRörelsens kostnader\nDriftkostnader\nEl\t\t\t\t\t\t-193 200\t\t-142 300\nVärme\t\t\t\t\t-421 300\t\t-312 400\nVatten och avlopp\t\t\t-126 700\t\t-119 500\nSophämtning\t\t\t\t-85 900\t\t\t-82 300\nFastighetsskötsel\t\t\t-243 600\t\t-231 400\nReparationer\t\t\t\t-102 400\t\t-87 600\nUnderhåll\t\t\t\t-310 000\t\t-175 000\nFastighetsskatt/avgift\t\t\t-86 100\t\t\t-86 100\nFastighetssförsäkring\t\t\t-124 300\t\t-118 200\nKabel-TV/Internet\t\t\t-96 400\t\t\t-96 400\nStyrelsekostnader\t\t\t-42 500\t\t\t-40 200\nFörvaltningsarvoden\t\t\t-185 800\t\t-180 400\nÖvriga driftkostnader\t\t\t-104 700\t\t-96 300\nSumma driftkostnader\t\t\t-2 122 900\t\t-1 768 100\n\nFinansiella poster\nRäntekostnader\t\t\t\t-712 300\t\t-401 200\nSumma finansiella poster\t\t-712 300\t\t-401 200\n\nÅrets resultat\t\t\t\t952 800\t\t1 614 600"
            },
            {
                "page_num": 5,
                "text": "TILLÄGGSUPPLYSNINGAR\n\nLån\n\nKreditgivare: Swedbank\nLånebelopp: 10 400 000 kr\nRäntesats: 3,75%\nBindningstid: 2024-09-15\n\nKreditgivare: SEB\nLånebelopp: 8 600 000 kr\nRäntesats: 4,25%\nBindningstid: 2026-03-25\n\nKreditgivare: Handelsbanken\nLånebelopp: 7 500 000 kr\nRäntesats: 3,50%\nBindningstid: 2025-06-30"
            }
        ]
    }
    
    with open(ocr_dir / "282645_årsredovisning__brf_trädgården_1_gustavsberg.pdf_ocr.json", 'w', encoding='utf-8') as f:
        json.dump(tradgarden_ocr, f, ensure_ascii=False, indent=2)
    
    print(f"Created Tradgarden sample pages in {ocr_dir}")

def create_sailor_samples():
    """Create sample pages for Sailor BRF."""
    ocr_dir = Path("./experiments/mistral_ocr_results")
    ensure_dir(ocr_dir)
    
    # Create Sailor sample
    sailor_ocr = {
        "document_id": "sailor_samples",
        "pages": [
            {
                "page_num": 1,
                "text": "BRF SAILOR\nORGANISATIONSNUMMER: 769634-2214\nÅRSREDOVISNING 2023\n\nBostadsrättsföreningen Sailor\nAdress: Sjövägen 5, 120 67 Stockholm\nTfn: 08-987 65 43\nE-post: info@brfsailor.se\nHemsida: www.brfsailor.se\n\nFastighetsbeteckning: Stockholm Masten 2:14\nTotal yta: 4 120 kvm\nBostadsyta (BOA): 3 860 kvm\nLokalyta (LOA): 260 kvm"
            },
            {
                "page_num": 2,
                "text": "STYRELSE OCH FUNKTIONÄRER\n\nStylelseledamöter\nOrdinarie ledamöter\nMaria Sjögren\t\tOrdförande\nPeter Ström\t\tSekreterare\nSofia Bäverdal\t\tKassör\nAnders Bergman\t\tLedamot\nLisa Storm\t\t\tLedamot\n\nSuppleanter\nJohan Skärgård\t\tSuppleant\nEllen Våg\t\t\tSuppleant\n\nRevisorer\nBjörn Ankare\t\tOrdinarie revisor, extern, KPMG\nJenny Sjöholm\t\tRevisorssuppleant, extern, KPMG\n\nValberedning\nNiklas Dyk\t\t\tSammankallande\nEmma Fiskare\t\tLedamot"
            },
            {
                "page_num": 3,
                "text": "RESULTATRÄKNING\n\nRörelsens intäkter\t\t\t\t2023\t\t\t2022\nÅrsavgifter\t\t\t\t\t4 632 000\t\t4 632 000\nHyresintäkter lokaler\t\t\t312 000\t\t\t312 000\nÖvriga intäkter\t\t\t\t76 500\t\t\t64 300\nSumma rörelsens intäkter\t\t5 020 500\t\t5 008 300\n\nRörelsens kostnader\nDriftkostnader\nEl\t\t\t\t\t\t-245 600\t\t-183 400\nVärme\t\t\t\t\t-534 700\t\t-412 500\nVatten och avlopp\t\t\t-168 300\t\t-159 200\nSophämtning\t\t\t\t-102 400\t\t-98 100\nFastighetsskötsel\t\t\t-312 500\t\t-298 700\nReparationer\t\t\t\t-143 200\t\t-126 300\nUnderhåll\t\t\t\t-420 000\t\t-210 000\nFastighetsskatt/avgift\t\t\t-103 000\t\t-103 000\nFastighetssförsäkring\t\t\t-142 800\t\t-136 500\nKabel-TV/Internet\t\t\t-103 200\t\t-103 200\nStyrelsekostnader\t\t\t-56 700\t\t\t-52 400\nFörvaltningsarvoden\t\t\t-213 600\t\t-207 500\nÖvriga driftkostnader\t\t\t-132 900\t\t-124 500\nSumma driftkostnader\t\t\t-2 678 900\t\t-2 215 300\n\nFinansiella poster\nRäntekostnader\t\t\t\t-978 400\t\t-642 300\nSumma finansiella poster\t\t-978 400\t\t-642 300\n\nÅrets resultat\t\t\t\t1 363 200\t\t2 150 700"
            },
            {
                "page_num": 4,
                "text": "LÅN OCH FINANSIERING\n\nKreditgivare: Nordea\nLånebelopp: 15 600 000 kr\nRäntesats: 3,85%\nBindningstid: 2025-03-30\nAmortering per år: 200 000 kr\n\nKreditgivare: SEB\nLånebelopp: 12 300 000 kr\nRäntesats: 4,15%\nBindningstid: 2026-11-15\nAmortering per år: 200 000 kr\n\nKreditgivare: Swedbank\nLånebelopp: 9 800 000 kr\nRäntesats: 3,95%\nBindningstid: 2024-08-20\nAmortering per år: 100 000 kr\n\nTotal låneskuld: 37 700 000 kr\nGenomsnittlig ränta: 3,98%\nLån per kvm bostadsyta: 9 767 kr/kvm"
            }
        ]
    }
    
    with open(ocr_dir / "282782_årsredovisning__brf_sailor.pdf_ocr.json", 'w', encoding='utf-8') as f:
        json.dump(sailor_ocr, f, ensure_ascii=False, indent=2)
        
    print(f"Created Sailor sample pages in {ocr_dir}")

def main():
    """Main function to create all sample pages."""
    print("Creating sample OCR pages for LLM extraction testing...")
    create_tradgarden_samples()
    create_sailor_samples()
    print("All sample pages created successfully.")

if __name__ == "__main__":
    main()