#!/usr/bin/env python3
"""
Test text extraction on machine-readable PDFs
"""

import fitz  # PyMuPDF
from pathlib import Path

def test_text_extraction():
    """Test text extraction on machine-readable PDFs"""
    
    machine_readable_pdfs = [
        "43848_ekonomisk_plan_lund_brf_lobo.pdf",
        "286626_ekonomisk_plan__brf_västerport_12.pdf"
    ]
    
    print("🔍 TESTING TEXT EXTRACTION ON MACHINE-READABLE PDFs")
    print("="*80)
    
    for pdf_path in machine_readable_pdfs:
        if not Path(pdf_path).exists():
            print(f"❌ {pdf_path} not found")
            continue
            
        print(f"\n📄 PROCESSING: {pdf_path}")
        print("-" * 60)
        
        try:
            pdf_doc = fitz.open(pdf_path)
            
            for page_num in range(min(2, len(pdf_doc))):  # First 2 pages
                print(f"\n📄 PAGE {page_num + 1}:")
                print("-" * 40)
                
                page = pdf_doc[page_num]
                text = page.get_text()
                
                if text and len(text.strip()) > 50:
                    # Show clean text sections
                    lines = text.split('\n')
                    clean_lines = []
                    
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 3:
                            # Skip lines that are mostly special characters
                            if len([c for c in line if c.isalnum()]) / len(line) > 0.5:
                                clean_lines.append(line)
                    
                    # Group into sections
                    current_section = []
                    sections = []
                    
                    for line in clean_lines:
                        if (line.isupper() and len(line) > 5) or any(word in line.lower() for word in ['ekonomisk', 'plan', 'brf', 'förening']):
                            # Likely header
                            if current_section:
                                sections.append('\n'.join(current_section))
                            current_section = [line]
                        else:
                            current_section.append(line)
                    
                    if current_section:
                        sections.append('\n'.join(current_section))
                    
                    print(f"📝 TEXT SECTIONS FOUND: {len(sections)}")
                    for i, section in enumerate(sections[:3], 1):  # Show first 3
                        preview = section[:200] + "..." if len(section) > 200 else section
                        print(f"  Section {i}: {preview}")
                        print()
                        
                else:
                    print("❌ No meaningful text found")
                    
            pdf_doc.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*80)
    print("✅ TEXT EXTRACTION TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_text_extraction()