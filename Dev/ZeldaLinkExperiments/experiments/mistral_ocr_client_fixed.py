#!/usr/bin/env python3
"""
Mistral OCR Client - Updated to match official SDK approach
"""

import os
import sys
import base64
import json
import argparse
from pathlib import Path

# Try to import Mistral AI SDK, install if needed
try:
    from mistralai import Mistral
except ImportError:
    print("Installing mistralai SDK...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mistralai", "--break-system-packages"])
    from mistralai import Mistral

# Verify needed constants are set
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

def process_pdf_with_ocr(pdf_path, output_path=None):
    """
    Process a PDF file with Mistral OCR API using the official SDK.
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Path to save the OCR results
        
    Returns:
        OCR results
    """
    print(f"Processing PDF with Mistral OCR: {os.path.basename(pdf_path)}")
    
    # Initialize Mistral client
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    # Verify PDF exists
    pdf_file = Path(pdf_path)
    if not pdf_file.is_file():
        print(f"Error: PDF file not found at {pdf_path}")
        return None
    
    try:
        # Upload the PDF file
        print("Uploading PDF to Mistral...")
        uploaded_file = client.files.upload(
            file={
                "file_name": pdf_file.stem,
                "content": pdf_file.read_bytes(),
            },
            purpose="ocr"
        )
        print(f"File uploaded successfully with ID: {uploaded_file.id}")
        
        # Get URL for the uploaded file
        signed_url = client.files.get_signed_url(file_id=uploaded_file.id)
        print("Got signed URL for the file")
        
        # Process PDF with OCR
        print("Processing with OCR...")
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": signed_url.url
            },
            include_image_base64=True
        )
        
        # Convert response to dictionary
        response_dict = json.loads(ocr_response.model_dump_json())
        
        # Determine output path if not specified
        if not output_path:
            output_dir = "mistral_ocr_results"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{os.path.basename(pdf_path)}_ocr.md")
        
        # Extract markdown content
        markdown_content = ""
        for i, page in enumerate(ocr_response.pages):
            # Use index+1 as page number if page_number attribute is not available
            page_num = getattr(page, 'page_number', i+1)
            markdown_content += f"\n\n## Page {page_num}\n\n{page.markdown}\n\n"
        
        # Save text content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Saved OCR results to {output_path}")
        
        # Save JSON response
        json_path = os.path.splitext(output_path)[0] + ".json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(response_dict, f, ensure_ascii=False, indent=2)
        print(f"Saved raw OCR JSON to {json_path}")
        
        return response_dict
    
    except Exception as e:
        print(f"Error processing PDF with OCR: {e}")
        return None

def process_image_with_ocr(image_path, output_path=None):
    """
    Process an image file with Mistral OCR API using the official SDK.
    
    Args:
        image_path: Path to the image file
        output_path: Path to save the OCR results
        
    Returns:
        OCR results
    """
    print(f"Processing image with Mistral OCR: {os.path.basename(image_path)}")
    
    # Initialize Mistral client
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    # Verify image exists
    image_file = Path(image_path)
    if not image_file.is_file():
        print(f"Error: Image file not found at {image_path}")
        return None
    
    try:
        # Encode image to base64
        encoded_image = base64.b64encode(image_file.read_bytes()).decode()
        base64_data_url = f"data:image/jpeg;base64,{encoded_image}"
        
        # Process image with OCR
        print("Processing with OCR...")
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": base64_data_url
            }
        )
        
        # Convert response to dictionary
        response_dict = json.loads(ocr_response.model_dump_json())
        
        # Determine output path if not specified
        if not output_path:
            output_dir = "mistral_ocr_results"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{os.path.basename(image_path)}_ocr.md")
        
        # Extract markdown content
        markdown_content = ""
        for i, page in enumerate(ocr_response.pages):
            # Use index+1 as page number if page_number attribute is not available
            page_num = getattr(page, 'page_number', i+1)
            markdown_content += f"\n## Page {page_num}\n\n{page.markdown}\n\n"
        
        # Save text content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Saved OCR results to {output_path}")
        
        # Save JSON response
        json_path = os.path.splitext(output_path)[0] + ".json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(response_dict, f, ensure_ascii=False, indent=2)
        print(f"Saved raw OCR JSON to {json_path}")
        
        return response_dict
    
    except Exception as e:
        print(f"Error processing image with OCR: {e}")
        return None

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Process a file with Mistral OCR API")
    parser.add_argument("--file", "-f", required=True, help="Path to the file (PDF or image)")
    parser.add_argument("--output", "-o", help="Path to save the OCR results")
    
    args = parser.parse_args()
    
    # Load API key from .env.backup if available
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.backup")
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith("MISTRAL_API_KEY="):
                    os.environ["MISTRAL_API_KEY"] = line.strip().split("=", 1)[1]
                    print(f"Loaded API key from .env.backup")
    
    # Get API key from environment
    global MISTRAL_API_KEY
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
    
    if not MISTRAL_API_KEY:
        print("Error: MISTRAL_API_KEY environment variable is not set")
        return 1
    
    # Check file extension to determine processing method
    file_path = args.file
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        result = process_pdf_with_ocr(file_path, args.output)
    elif file_ext in ['.jpg', '.jpeg', '.png']:
        result = process_image_with_ocr(file_path, args.output)
    else:
        print(f"Unsupported file type: {file_ext}")
        print("Supported types: .pdf, .jpg, .jpeg, .png")
        return 1
    
    if result:
        print("OCR processing completed successfully!")
        return 0
    else:
        print("OCR processing failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())