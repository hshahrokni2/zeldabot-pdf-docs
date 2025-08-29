#!/usr/bin/env python3
"""
Direct H100 Sectioning Runner (No Flask)
Runs HF Qwen2.5-VL directly on H100 with receipts and bounded prompts
"""

import os
import json
import time
import hashlib
import hmac
import uuid
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

# Only import on H100
try:
    import torch
    from transformers import Qwen2_5_VLForConditionalGeneration, Qwen2_5_VLProcessor
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

class DirectH100Sectioner:
    def __init__(self, model_repo: str, receipts_dir: str, hmac_key: str):
        if not HF_AVAILABLE:
            raise RuntimeError("This script must run on H100 with transformers installed")
            
        self.model_repo = model_repo
        self.receipts_dir = Path(receipts_dir)
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.hmac_key = hmac_key.encode('utf-8')
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        print(f"🔧 Loading {model_repo} on {self.device}...")
        print(f"🎯 GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
        
        self.processor = Qwen2_5_VLProcessor.from_pretrained(model_repo)
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_repo,
            device_map=self.device,
            dtype=torch.bfloat16,
            trust_remote_code=True
        )
        print(f"✅ Model loaded successfully")
    
    def create_receipt(self, call_id: str, prompt_text: str, image_sha: str, 
                      response: str, latency_ms: int, page_num: int) -> str:
        """Create HMAC-verified receipt for anti-simulation"""
        receipt = {
            "call_id": call_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_repo": self.model_repo,
            "device": self.device,
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "page_number": page_num,
            "prompt_sha256": hashlib.sha256(prompt_text.encode()).hexdigest()[:16],
            "image_sha256": image_sha,
            "response_sha256": hashlib.sha256(response.encode()).hexdigest()[:16],
            "latency_ms": latency_ms,
            "origin": "DIRECT_H100_QWEN",
            "vision_only": True,
            "no_ocr_fallback": True
        }
        
        # Create HMAC signature for anti-simulation
        receipt_data = f"{call_id}||{image_sha}||{page_num}".encode('utf-8')
        receipt["hmac"] = hmac.new(self.hmac_key, receipt_data, hashlib.sha256).hexdigest()
        
        # Save receipt
        receipt_path = self.receipts_dir / f"{call_id}.json"
        with open(receipt_path, 'w') as f:
            json.dump(receipt, f, indent=2)
            
        return receipt_path.as_posix()
    
    def extract_page_image(self, pdf_path: str, page_num: int, 
                          dpi: int = 135, max_side: int = 1600,
                          jpeg_quality: int = 85) -> Tuple[Image.Image, str]:
        """Extract page as PIL Image with size constraints"""
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]  # 0-indexed
        
        # Calculate matrix for target DPI
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(BytesIO(img_data))
        
        # Resize if too large
        if max(image.size) > max_side:
            ratio = max_side / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to JPEG for consistent hashing
        jpeg_buffer = BytesIO()
        image.save(jpeg_buffer, format='JPEG', quality=jpeg_quality, optimize=True)
        jpeg_bytes = jpeg_buffer.getvalue()
        
        # Create SHA256 for receipt
        image_sha = hashlib.sha256(jpeg_bytes).hexdigest()[:16]
        
        doc.close()
        return image, image_sha
    
    def load_bounded_prompt(self, prompt_path: str) -> str:
        """Load the 88-word bounded prompt"""
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
        
        # Verify word count ≤ 120 
        word_count = len(prompt.split())
        if word_count > 120:
            raise ValueError(f"Prompt too long: {word_count} words (max 120)")
            
        return prompt
    
    def extract_headers_from_page(self, image: Image.Image, prompt: str, page_num: int) -> Dict[str, Any]:
        """Extract headers from single page using HF Qwen"""
        call_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Create conversation for Qwen
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": f"{prompt}\n\nPage number: {page_num}"}
                    ]
                }
            ]
            
            # Apply chat template
            text = self.processor.apply_chat_template(
                conversation, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            # Process inputs
            inputs = self.processor(
                text=[text],
                images=[image],
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            # Generate with strict settings
            with torch.no_grad():
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=False,  # Deterministic
                    temperature=0.0,
                    pad_token_id=self.processor.tokenizer.pad_token_id
                )
            
            # Decode response
            input_length = inputs['input_ids'].shape[1]
            new_tokens = output_ids[0][input_length:]
            response = self.processor.tokenizer.decode(new_tokens, skip_special_tokens=True)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "call_id": call_id,
                "response": response,
                "latency_ms": latency_ms,
                "page": page_num,
                "input_tokens": input_length,
                "output_tokens": len(new_tokens)
            }
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "call_id": call_id,
                "error": str(e),
                "latency_ms": latency_ms,
                "page": page_num
            }
    
    def extract_json_from_response(self, response_text: str) -> List[Dict]:
        """Extract JSON array from model response"""
        import re
        
        # Look for JSON array pattern
        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
        if not json_match:
            # Try to find any curly brace content
            json_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
            if json_match:
                # Wrap single object in array
                json_str = f"[{json_match.group(0)}]"
            else:
                return []
        else:
            json_str = json_match.group(0)
        
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                return []
        except json.JSONDecodeError:
            return []
    
    def process_pdf_direct(self, pdf_path: str, prompt_path: str, 
                          output_path: str, run_id: str) -> Dict[str, Any]:
        """Process entire PDF directly on H100"""
        
        if not os.path.exists(pdf_path):
            return {"error": f"PDF not found: {pdf_path}"}
            
        if not os.path.exists(prompt_path):
            return {"error": f"Prompt not found: {prompt_path}"}
        
        prompt = self.load_bounded_prompt(prompt_path)
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()
        
        print(f"📄 Processing {total_pages} pages from {pdf_path}")
        print(f"📝 Using {len(prompt.split())}-word bounded prompt")
        print(f"🎯 Output: {output_path}")
        print(f"📄 Receipts: {self.receipts_dir}")
        
        results = {
            "run_id": run_id,
            "pdf_path": pdf_path,
            "prompt_path": prompt_path,
            "total_pages": total_pages,
            "device": self.device,
            "model_repo": self.model_repo,
            "pages": []
        }
        
        total_headers = 0
        total_latency = 0
        
        for page_num in range(1, total_pages + 1):
            print(f"\n📄 Processing page {page_num}/{total_pages}...")
            
            try:
                # Extract page image  
                image, image_sha = self.extract_page_image(pdf_path, page_num)
                
                # Process with HF Qwen
                result = self.extract_headers_from_page(image, prompt, page_num)
                
                if result["success"]:
                    # Extract JSON from response
                    headers = self.extract_json_from_response(result["response"])
                    
                    # Create receipt
                    receipt_path = self.create_receipt(
                        result["call_id"], prompt, image_sha,
                        result["response"], result["latency_ms"], page_num
                    )
                    
                    print(f"   ✅ Found {len(headers)} headers ({result['latency_ms']}ms)")
                    print(f"   🧾 Receipt: {receipt_path}")
                    
                    page_result = {
                        "page": page_num,
                        "success": True,
                        "headers": headers,
                        "raw_response": result["response"],
                        "image_sha": image_sha,
                        "receipt_path": receipt_path,
                        "latency_ms": result["latency_ms"],
                        "call_id": result["call_id"],
                        "tokens": {
                            "input": result.get("input_tokens", 0),
                            "output": result.get("output_tokens", 0)
                        }
                    }
                    
                    total_headers += len(headers)
                    total_latency += result["latency_ms"]
                    
                else:
                    print(f"   ❌ Error: {result['error']}")
                    page_result = {
                        "page": page_num,
                        "success": False,
                        "error": result["error"],
                        "image_sha": image_sha,
                        "latency_ms": result["latency_ms"],
                        "call_id": result["call_id"]
                    }
                
                results["pages"].append(page_result)
                
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                results["pages"].append({
                    "page": page_num,
                    "success": False,
                    "error": str(e)
                })
        
        # Add summary stats
        results["summary"] = {
            "total_headers": total_headers,
            "total_latency_ms": total_latency,
            "avg_latency_ms": total_latency / total_pages if total_pages > 0 else 0,
            "success_pages": sum(1 for p in results["pages"] if p.get("success", False))
        }
        
        # Save results
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to {output_path}")
        print(f"📊 Summary: {total_headers} headers, {results['summary']['success_pages']}/{total_pages} pages, avg {results['summary']['avg_latency_ms']:.1f}ms")
        
        return results

def main():
    parser = argparse.ArgumentParser(description="Direct H100 Sectioning Runner")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")  
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--run-id", required=True, help="Run ID for receipts")
    parser.add_argument("--prompt", default="prompts/prompt_header_agent_v3.txt", help="Prompt file")
    args = parser.parse_args()
    
    # Required environment variables
    model_repo = os.getenv("QWEN_MODEL_REPO", "Qwen/Qwen2.5-VL-7B-Instruct")
    receipts_dir = os.getenv("RECEIPTS_DIR", "receipts/sectioning")  
    hmac_key = os.getenv("RECEIPT_HMAC_KEY")
    
    if not hmac_key:
        print("❌ RECEIPT_HMAC_KEY environment variable required")
        return 1
    
    # Initialize sectioner
    sectioner = DirectH100Sectioner(model_repo, receipts_dir, hmac_key)
    
    # Process PDF
    result = sectioner.process_pdf_direct(args.pdf, args.prompt, args.out, args.run_id)
    
    if "error" in result:
        print(f"❌ Failed: {result['error']}")
        return 1
    
    print("🎉 Direct H100 sectioning complete!")
    return 0

if __name__ == "__main__":
    exit(main())