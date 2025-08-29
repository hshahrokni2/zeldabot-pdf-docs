#!/usr/bin/env python3
"""
H100 SSH Diagnostic BRF Extractor - Show exact prompts, endpoints, and returns
Runs on H100 via SSH to diagnose why Qwen2.5-VL-7B isn't processing actual visual content
"""

import os
import sys
import tempfile
import subprocess

def create_h100_diagnostic_script():
    """Create the diagnostic script to run on H100"""
    script_content = '''#!/usr/bin/env python3
"""
H100 Diagnostic BRF Extractor - Run on H100 with CUDA
"""

import os
import json
import fitz
import torch
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, Qwen2_5_VLProcessor
import time
from pathlib import Path

class DiagnosticH100BRFExtractor:
    def __init__(self):
        self.model_path = "Qwen/Qwen2.5-VL-7B-Instruct"
        self.device = "cuda:0"
        
        print("🔧 Loading Qwen2.5-VL-7B model for diagnostics...")
        self.processor = Qwen2_5_VLProcessor.from_pretrained(self.model_path)
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_path,
            device_map=self.device,
            dtype=torch.bfloat16,
            trust_remote_code=True
        )
        print("✅ Model loaded successfully")

    def create_extraction_prompt(self, page_num: int) -> str:
        """Create the exact prompt being sent to the model - REVISED for better recall"""
        return f"""You are analyzing page {page_num} of a Swedish BRF (housing cooperative) economic plan or annual report PDF to extract visible headers.

GUIDELINES:
1. Identify text that appears as headers or headings based on visual cues like larger font, bold, centering, uppercase, or section breaks.
2. Include note references like "Not 1", "Not 2" if they stand out as individual items.
3. Err on the side of inclusion if the text seems formatted differently from body paragraphs.
4. Common headers may include terms like "FÖRVALTNINGSBERÄTTELSE", "BALANSRÄKNING", "RESULTATRÄKNING", "Noter", or subsections like "Driftskostnader".

EXAMPLES OF HEADERS TO EXTRACT:
- "FÖRVALTNINGSBERÄTTELSE" (main section, level 1)
- "Balansräkning" (section title, level 1)
- "Not 15 Övriga skulder" (note heading, level 3)
- "Driftskostnader per m²" (subsection, level 2)

Extract all headers visible on THIS SPECIFIC PAGE {page_num} and classify by hierarchy:
- Level 1: Main section headers (e.g., FÖRVALTNINGSBERÄTTELSE, RESULTATRÄKNING)
- Level 2: Subsections (e.g., Driftskostnader, Underhållskostnader)
- Level 3: Individual notes/items (e.g., Not 1, Not 2, specific line items)

Return ONLY a valid JSON array of extracted headers:
[{{"header": "exact text", "level": 1-3, "start_page": {page_num}, "end_page": {page_num}}}]

If truly no headers are visible, return: []"""

    def extract_page_image(self, pdf_path: str, page_num: int) -> Image.Image:
        """Extract single page as image at DPI=200"""
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]
        
        # Convert to image at DPI=200
        mat = fitz.Matrix(200/72, 200/72)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        # Convert to PIL Image
        from io import BytesIO
        image = Image.open(BytesIO(img_data))
        doc.close()
        
        return image

    def diagnose_single_page(self, pdf_path: str, page_num: int):
        """Diagnose extraction for a single page - show everything"""
        print(f"\\n{'='*60}")
        print(f"🔍 DIAGNOSTIC ANALYSIS - PAGE {page_num}")
        print(f"{'='*60}")
        
        # 1. Show the exact prompt
        prompt = self.create_extraction_prompt(page_num)
        print(f"\\n📝 EXACT PROMPT BEING SENT:")
        print(f"{'─'*40}")
        print(prompt)
        print(f"{'─'*40}")
        
        # 2. Extract page image
        print(f"\\n🖼️ EXTRACTING PAGE {page_num} IMAGE...")
        image = self.extract_page_image(pdf_path, page_num)
        print(f"   Image size: {image.size}")
        print(f"   Image mode: {image.mode}")
        
        # 3. Show processor call details
        print(f"\\n🔧 PROCESSOR CALL DETAILS:")
        print(f"   Endpoint: processor.apply_chat_template()")
        print(f"   Method: Chat template format with image+text")
        
        # Create conversation
        conversation = [
            {
                "role": "user", 
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        print(f"   Conversation structure: {len(conversation)} messages")
        print(f"   Content types: image + text")
        
        # 4. Apply chat template
        print(f"\\n⚙️ APPLYING CHAT TEMPLATE...")
        start_time = time.time()
        
        try:
            text = self.processor.apply_chat_template(
                conversation, 
                tokenize=False, 
                add_generation_prompt=True
            )
            template_time = time.time() - start_time
            print(f"   ✅ Chat template applied ({template_time:.2f}s)")
            print(f"   Template length: {len(text)} characters")
            
            # Show first/last 200 chars of template
            print(f"\\n📄 CHAT TEMPLATE OUTPUT (first 200 chars):")
            print(f"'{text[:200]}...'")
            print(f"\\n📄 CHAT TEMPLATE OUTPUT (last 200 chars):")
            print(f"'...{text[-200:]}'")
            
        except Exception as e:
            print(f"   ❌ Chat template failed: {e}")
            return
        
        # 5. Process inputs
        print(f"\\n🔄 PROCESSING INPUTS...")
        try:
            inputs = self.processor(
                text=[text],
                images=[image], 
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            print(f"   ✅ Inputs processed")
            print(f"   Input IDs shape: {inputs['input_ids'].shape}")
            print(f"   Pixel values shape: {inputs.get('pixel_values', 'None').shape if 'pixel_values' in inputs else 'No pixel values'}")
            
        except Exception as e:
            print(f"   ❌ Input processing failed: {e}")
            return
        
        # 6. Model generation
        print(f"\\n🤖 MODEL GENERATION...")
        gen_start = time.time()
        
        try:
            with torch.no_grad():
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    do_sample=False,
                    temperature=0.0,
                    pad_token_id=self.processor.tokenizer.pad_token_id
                )
            
            gen_time = time.time() - gen_start
            print(f"   ✅ Generation completed ({gen_time:.2f}s)")
            print(f"   Output shape: {output_ids.shape}")
            
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            return
        
        # 7. Decode output
        print(f"\\n📤 DECODING OUTPUT...")
        try:
            # Get only the new tokens (skip input)
            input_length = inputs['input_ids'].shape[1]
            new_tokens = output_ids[0][input_length:]
            
            raw_output = self.processor.tokenizer.decode(
                new_tokens, 
                skip_special_tokens=True
            )
            
            print(f"   ✅ Output decoded")
            print(f"   Raw output length: {len(raw_output)} characters")
            
        except Exception as e:
            print(f"   ❌ Decoding failed: {e}")
            return
        
        # 8. Show RAW model output
        print(f"\\n🔍 RAW MODEL OUTPUT:")
        print(f"{'─'*40}")
        print(f"'{raw_output}'")
        print(f"{'─'*40}")
        
        # 9. Try JSON extraction
        print(f"\\n🧹 JSON CLEANING ATTEMPT...")
        try:
            # Clean whitespace
            clean_output = raw_output.strip()
            
            # Look for JSON structure
            import re
            json_match = re.search(r'\\[.*\\]', clean_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                print(f"   ✅ JSON pattern found")
                print(f"   Extracted: '{json_str}'")
                
                # Parse JSON
                try:
                    parsed = json.loads(json_str)
                    print(f"   ✅ JSON parsed successfully")
                    print(f"   Headers found: {len(parsed)}")
                    
                    for i, header in enumerate(parsed):
                        print(f"     {i+1}. {header}")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON parsing failed: {e}")
                    print(f"   JSON string: '{json_str}'")
                    
            else:
                print(f"   ❌ No JSON array pattern found")
                print(f"   Looking for other patterns...")
                
        except Exception as e:
            print(f"   ❌ JSON cleaning failed: {e}")
        
        print(f"\\n{'='*60}")
        print(f"DIAGNOSTIC COMPLETE - PAGE {page_num}")
        print(f"{'='*60}")

def main():
    """Run diagnostic on specific pages"""
    pdf_path = "/tmp/sjostaden2_arsredovisning.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print("🚀 Starting H100 BRF Diagnostic Extractor")
    print(f"📄 Target PDF: {pdf_path}")
    
    extractor = DiagnosticH100BRFExtractor()
    
    # Test specific pages with Noter headers from Sjöstaden 2 årsredovisning
    test_pages = [2, 11, 12, 13, 14, 15, 16]  # Table of contents + Noter pages 11-16
    
    for page_num in test_pages:
        try:
            extractor.diagnose_single_page(pdf_path, page_num)
        except Exception as e:
            print(f"❌ Diagnostic failed for page {page_num}: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\\n" + "="*80 + "\\n")

if __name__ == "__main__":
    main()
'''
    return script_content

def run_diagnostic_on_h100():
    """Run the diagnostic script on H100 via SSH"""
    print("🚀 Running diagnostic on H100 via SSH...")
    
    # Create temporary script file
    script_content = create_h100_diagnostic_script()
    
    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        temp_script = f.name
    
    print(f"📝 Created temp script: {temp_script}")
    
    try:
        # Use Sjöstaden 2 årsredovisning that should already be on H100
        print("📤 Using Sjöstaden 2 årsredovisning on H100...")
        pdf_path = "/tmp/sjostaden2_arsredovisning.pdf"
        
        # Copy Sjöstaden 2 from known location
        scp_pdf_cmd = [
            "scp", "-i", "/Users/hosseins/.ssh/BrfGraphRag", "-P", "26983",
            "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/Ground Truth, Schema, Mappings/arsredovisning_2024_brf_sjostaden_2_komplett_med_revisionsberattelse.pdf",
            f"root@45.135.56.10:/tmp/sjostaden2_arsredovisning.pdf"
        ]
        
        subprocess.run(scp_pdf_cmd, check=True)
        print("✅ Sjöstaden 2 PDF copied to H100")
        
        # Copy script to H100
        print("📤 Copying diagnostic script to H100...")
        scp_script_cmd = [
            "scp", "-i", "/Users/hosseins/.ssh/BrfGraphRag", "-P", "26983",
            temp_script,
            f"root@45.135.56.10:/tmp/h100_diagnostic.py"
        ]
        
        subprocess.run(scp_script_cmd, check=True)
        print("✅ Script copied to H100")
        
        # Run diagnostic script on H100
        print("🔬 Running diagnostic on H100...")
        ssh_cmd = [
            "ssh", "-i", "/Users/hosseins/.ssh/BrfGraphRag", "-p", "26983",
            "root@45.135.56.10",
            "cd /tmp && python3 h100_diagnostic.py"
        ]
        
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=600)
        
        print("📊 H100 DIAGNOSTIC RESULTS:")
        print("="*60)
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ STDERR:")
            print(result.stderr)
        
        print(f"Exit code: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print("⏰ Diagnostic timed out after 10 minutes")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
    except Exception as e:
        print(f"❌ Error running diagnostic: {e}")
    finally:
        # Cleanup temp file
        os.unlink(temp_script)

if __name__ == "__main__":
    run_diagnostic_on_h100()