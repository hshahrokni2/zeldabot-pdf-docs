#!/usr/bin/env python3
"""
Enhanced OCR+Vision Processor for BRF Trädgården

This specialized script implements an optimized extraction approach for the BRF Trädgården
scanned document, using advanced OCR preprocessing, optimized vision prompts,
multi-page analysis, and intelligent results merging.
"""

import os
import argparse
import logging
import json
import tempfile
import time
import re
import base64
import io
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# Import computer vision and PDF processing libraries
import cv2
import numpy as np
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pdf2image

# Import LLM/API libraries
import requests
import openai
from dotenv import load_dotenv
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tradgarden_extraction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("tradgarden_enhanced")

# Load environment variables
load_dotenv()
API_KEY = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY")

# Configuration
OCR_LANGUAGE = "swe"  # Swedish
DPI = 400  # Higher DPI for better OCR quality on scanned documents
PAGE_LIMIT = None  # Process all pages by default
OUTPUT_DIR = "tradgarden_results"
CONFIDENCE_THRESHOLD = 50  # Minimum confidence score (0-100) for extracted values

# Qwen VL Max API configuration
VISION_API_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL = "qwen-vl-max"


class EnhancedTradgardenProcessor:
    """
    Enhanced processor for BRF Trädgården scanned document
    """
    
    def __init__(self, pdf_path: str, api_key: str, output_dir: str = OUTPUT_DIR,
                 dpi: int = DPI, ocr_lang: str = OCR_LANGUAGE,
                 confidence_threshold: int = CONFIDENCE_THRESHOLD):
        """
        Initialize the enhanced processor
        
        Args:
            pdf_path: Path to the PDF document
            api_key: API key for Qwen VL Max
            output_dir: Directory for output files
            dpi: DPI for OCR preprocessing
            ocr_lang: Language for OCR
            confidence_threshold: Minimum confidence score for extracted values
        """
        self.pdf_path = os.path.abspath(pdf_path)
        self.api_key = api_key
        self.output_dir = output_dir
        self.dpi = dpi
        self.ocr_lang = ocr_lang
        self.confidence_threshold = confidence_threshold
        self.filename = os.path.basename(pdf_path)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create subdirectories for intermediate results
        self.ocr_dir = os.path.join(output_dir, "ocr_results")
        self.vision_dir = os.path.join(output_dir, "vision_results")
        self.processed_images_dir = os.path.join(output_dir, "processed_images")
        os.makedirs(self.ocr_dir, exist_ok=True)
        os.makedirs(self.vision_dir, exist_ok=True)
        os.makedirs(self.processed_images_dir, exist_ok=True)
        
        # Initialize API client for vision analysis
        openai.api_key = api_key
        openai.api_base = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        
        # Load document
        self.doc = fitz.open(pdf_path)
        self.page_count = len(self.doc)
        logger.info(f"Loaded document: {pdf_path} with {self.page_count} pages")
        
        # Initialize results
        self.ocr_results = {}
        self.vision_results = {}
        self.combined_results = {
            "costs": {},
            "property_info": {
                "property_designation": None,
                "total_area": None,
                "residential_area": None,
                "commercial_area": None,
                "apartment_count": None,
                "year_built": None,
                "tax_value": None
            },
            "income_statement": {
                "total_revenue": None,
                "total_expenses": None,
                "profit_loss": None,
                "operating_costs": {},
                "financial_items": {},
                "comparison_year": None,
                "current_year": None
            },
            "balance_sheet": {
                "assets": {
                    "current_assets": None,
                    "fixed_assets": None,
                    "total_assets": None
                },
                "liabilities": {
                    "short_term_liabilities": None,
                    "long_term_liabilities": None,
                    "total_liabilities": None
                },
                "equity": None
            },
            "extraction_metadata": {
                "enhanced_tradgarden_extraction": True,
                "extraction_timestamp": datetime.now().isoformat(),
                "ocr_extraction_used": True,
                "vision_extraction_used": True,
                "ocr_language": ocr_lang,
                "ocr_dpi": dpi,
                "llm_model": MODEL,
                "filename": self.filename,
                "extracted_values_count": 0,
                "average_confidence": 0
            },
            "maintenance_info": {
                "historical_maintenance": [],
                "planned_maintenance": []
            }
        }
        
        # Track confidence scores for extracted values
        self.confidence_scores = {}
        
    def process(self) -> Dict[str, Any]:
        """
        Process the document with enhanced OCR+Vision approach
        
        Returns:
            Dictionary with extraction results
        """
        try:
            logger.info(f"Starting enhanced OCR+Vision processing for {self.filename}")
            
            # Step 1: Convert PDF to optimized images with preprocessing
            page_images = self._preprocess_pdf_pages()
            
            # Step 2: Perform OCR on preprocessed images
            logger.info("Performing OCR extraction on preprocessed images")
            self.ocr_results = self._perform_ocr(page_images)
            
            # Save OCR results
            ocr_output_path = os.path.join(self.ocr_dir, f"{self.filename}_ocr_enhanced.json")
            with open(ocr_output_path, 'w', encoding='utf-8') as f:
                json.dump(self.ocr_results, f, ensure_ascii=False, indent=2)
            logger.info(f"OCR results saved to {ocr_output_path}")
            
            # Step 3: Perform vision-based extraction
            logger.info("Performing vision-based extraction")
            self.vision_results = self._perform_vision_extraction(page_images)
            
            # Save vision results
            vision_output_path = os.path.join(self.vision_dir, f"{self.filename}_vision_enhanced.json")
            with open(vision_output_path, 'w', encoding='utf-8') as f:
                json.dump(self.vision_results, f, ensure_ascii=False, indent=2)
            logger.info(f"Vision results saved to {vision_output_path}")
            
            # Step 4: Combine results with intelligent merging
            logger.info("Combining OCR and vision results")
            self.combined_results = self._merge_results(self.ocr_results, self.vision_results)
            
            # Step 5: Post-process results for consistency
            logger.info("Post-processing results")
            self._post_process_results()
            
            # Save combined results
            combined_output_path = os.path.join(self.output_dir, f"{self.filename}_enhanced_results.json")
            with open(combined_output_path, 'w', encoding='utf-8') as f:
                json.dump(self.combined_results, f, ensure_ascii=False, indent=2)
            logger.info(f"Combined results saved to {combined_output_path}")
            
            # Print summary of extraction
            self._print_extraction_summary()
            
            return self.combined_results
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "filename": self.filename,
                "extraction_timestamp": datetime.now().isoformat()
            }
            
    def _preprocess_pdf_pages(self) -> List[Dict[str, Any]]:
        """
        Convert PDF pages to optimized images with enhanced preprocessing
        
        Returns:
            List of dictionaries with processed images and metadata
        """
        page_images = []
        
        # Determine pages to process
        pages_to_process = range(self.page_count)
        if PAGE_LIMIT is not None:
            pages_to_process = range(min(PAGE_LIMIT, self.page_count))
        
        # Convert PDF to images with pdf2image for higher quality
        logger.info(f"Converting PDF to images with DPI={self.dpi}")
        pdf_images = pdf2image.convert_from_path(
            self.pdf_path,
            dpi=self.dpi,
            thread_count=os.cpu_count() or 4,
            output_folder=tempfile.gettempdir(),
            fmt="png"
        )
        
        # Process each page with optimized preprocessing
        for i, img in tqdm(enumerate(pdf_images), total=len(pdf_images), desc="Preprocessing pages"):
            if i not in pages_to_process:
                continue
                
            # Apply advanced preprocessing for scanned documents
            processed_img = self._enhance_image_for_ocr(img)
            
            # Save processed image
            processed_img_path = os.path.join(self.processed_images_dir, f"page_{i+1}.png")
            processed_img.save(processed_img_path)
            
            # Convert to base64 for vision API
            buffered = io.BytesIO()
            processed_img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # Create page image entry
            page_images.append({
                "page_number": i + 1,
                "image": processed_img,
                "image_path": processed_img_path,
                "base64": img_base64
            })
            
        logger.info(f"Converted {len(page_images)} pages to optimized images")
        return page_images
        
    def _enhance_image_for_ocr(self, img: Image.Image) -> Image.Image:
        """
        Apply enhanced preprocessing to improve OCR quality for scanned documents
        
        Args:
            img: PIL Image object
            
        Returns:
            Processed PIL Image
        """
        # Convert to numpy array for OpenCV processing
        img_np = np.array(img)
        
        # Convert to grayscale if not already
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np
            
        # Apply adaptive thresholding for better text extraction from scanned documents
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Block size
            2    # Constant subtracted from mean
        )
        
        # Apply morphological operations to clean up noise
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Apply deskewing if the page is skewed
        coords = np.column_stack(np.where(opening > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust angle for rotations
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Only deskew if angle is significant (more than 0.5 degrees)
        if abs(angle) > 0.5:
            (h, w) = opening.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            deskewed = cv2.warpAffine(opening, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        else:
            deskewed = opening
            
        # Convert back to PIL Image
        enhanced_img = Image.fromarray(deskewed)
        
        # Apply additional PIL-based enhancements
        enhanced_img = enhanced_img.filter(ImageFilter.SHARPEN)
        enhancer = ImageEnhance.Contrast(enhanced_img)
        enhanced_img = enhancer.enhance(2.0)  # Enhance contrast
        
        return enhanced_img
    
    def _perform_ocr(self, page_images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform enhanced OCR on preprocessed images
        
        Args:
            page_images: List of page image dictionaries
            
        Returns:
            Dictionary with OCR results
        """
        ocr_results = {
            "costs": {},
            "property_info": {
                "property_designation": None,
                "total_area": None,
                "residential_area": None,
                "commercial_area": None,
                "apartment_count": None,
                "year_built": None,
                "tax_value": None
            },
            "income_statement": {
                "total_revenue": None,
                "total_expenses": None,
                "profit_loss": None,
                "operating_costs": {}
            },
            "balance_sheet": {
                "assets": {
                    "current_assets": None,
                    "fixed_assets": None,
                    "total_assets": None
                },
                "liabilities": {
                    "short_term_liabilities": None,
                    "long_term_liabilities": None,
                    "total_liabilities": None
                },
                "equity": None
            },
            "extraction_metadata": {
                "ocr_extraction": True,
                "language": self.ocr_lang,
                "dpi": self.dpi,
                "filename": self.filename,
                "page_results": {}
            },
            "page_texts": {}
        }
        
        # Process each page
        for page_data in tqdm(page_images, desc="OCR processing"):
            page_num = page_data["page_number"]
            img = page_data["image"]
            
            # Perform OCR with multiple configurations for best results
            config_results = []
            
            # Try different PSM (Page Segmentation Modes) for best results
            for psm in [6, 3, 4, 11]:
                config = f'--psm {psm} -l {self.ocr_lang}'
                
                text = pytesseract.image_to_string(img, config=config)
                
                # Basic evaluation of quality (count alphanumeric characters)
                quality = sum(1 for c in text if c.isalnum())
                
                config_results.append({
                    "text": text,
                    "quality": quality,
                    "config": config
                })
            
            # Select the best result
            best_result = max(config_results, key=lambda x: x["quality"])
            text = best_result["text"]
            
            # Store text for this page
            ocr_results["page_texts"][str(page_num)] = text
            
            # Extract information from OCR text
            page_extraction = self._extract_info_from_ocr_text(text, page_num)
            
            # Store page-specific results
            ocr_results["extraction_metadata"]["page_results"][str(page_num)] = {
                "extraction_quality": best_result["quality"],
                "config_used": best_result["config"],
                "extracted_fields": list(page_extraction.keys())
            }
            
            # Update main results with page extraction
            self._update_results_dict(ocr_results, page_extraction)
        
        return ocr_results
    
    def _extract_info_from_ocr_text(self, text: str, page_num: int) -> Dict[str, Any]:
        """
        Extract structured information from OCR text
        
        Args:
            text: OCR text
            page_num: Page number
            
        Returns:
            Dictionary with extracted information
        """
        page_extraction = {
            "confidence_scores": {}
        }
        
        # Pattern for property area (square meters)
        area_pattern = r'(\d[\d\s.,]*)(?:\s*kvm|\s*m²|\s*kvadratmeter)'
        area_matches = re.finditer(area_pattern, text, re.IGNORECASE)
        for match in area_matches:
            area_str = match.group(1).strip()
            area_str = re.sub(r'[^\d.,]', '', area_str).replace(',', '.')
            try:
                area = float(area_str)
                context = text[max(0, match.start() - 50):min(len(text), match.end() + 50)]
                
                # Categorize by context
                if "total" in context.lower() or "fastighet" in context.lower():
                    page_extraction["property_info.total_area"] = area
                    page_extraction["confidence_scores"]["property_info.total_area"] = 75
                elif "bostads" in context.lower() or "lägenhet" in context.lower():
                    page_extraction["property_info.residential_area"] = area
                    page_extraction["confidence_scores"]["property_info.residential_area"] = 75
                elif "lokal" in context.lower() or "kommersiell" in context.lower():
                    page_extraction["property_info.commercial_area"] = area
                    page_extraction["confidence_scores"]["property_info.commercial_area"] = 75
                else:
                    if "property_info.total_area" not in page_extraction:
                        page_extraction["property_info.total_area"] = area
                        page_extraction["confidence_scores"]["property_info.total_area"] = 60
            except ValueError:
                pass
                
        # Pattern for number of apartments
        apt_pattern = r'(\d+)\s*(?:st\.?|stycken)?\s*(?:bostadsrätts)?lägenheter'
        apt_matches = re.search(apt_pattern, text, re.IGNORECASE)
        if apt_matches:
            try:
                apt_count = int(apt_matches.group(1))
                page_extraction["property_info.apartment_count"] = apt_count
                page_extraction["confidence_scores"]["property_info.apartment_count"] = 80
            except ValueError:
                pass
        
        # Pattern for year built
        year_pattern = r'(?:byggår|byggnadsår|byggdes år|uppfört år|uppfördes år)\s*(?:är)?\s*(\d{4})'
        year_matches = re.search(year_pattern, text, re.IGNORECASE)
        if year_matches:
            try:
                year_built = int(year_matches.group(1))
                if 1800 <= year_built <= 2023:  # Reasonable range for Swedish buildings
                    page_extraction["property_info.year_built"] = year_built
                    page_extraction["confidence_scores"]["property_info.year_built"] = 80
            except ValueError:
                pass
        
        # Pattern for revenue
        revenue_pattern = r'(?:intäkter|rörelseintäkter|årsavgifter|nettoomsättning)[^\n]*?(\d[\d\s.,]*)(?:\s*tkr|\s*kkr|\s*mkr|\s*kr)?'
        revenue_matches = re.search(revenue_pattern, text, re.IGNORECASE)
        if revenue_matches:
            revenue_str = revenue_matches.group(1).strip()
            revenue_str = re.sub(r'[^\d.,]', '', revenue_str).replace(',', '.')
            try:
                revenue = float(revenue_str)
                
                # Check for unit multipliers
                if "tkr" in revenue_matches.group(0) or "kkr" in revenue_matches.group(0):
                    revenue *= 1000
                elif "mkr" in revenue_matches.group(0):
                    revenue *= 1000000
                    
                page_extraction["income_statement.total_revenue"] = revenue
                page_extraction["confidence_scores"]["income_statement.total_revenue"] = 75
            except ValueError:
                pass
        
        # Pattern for expenses
        expense_pattern = r'(?:kostnader|rörelsekostnader)[^\n]*?(\d[\d\s.,]*)(?:\s*tkr|\s*kkr|\s*mkr|\s*kr)?'
        expense_matches = re.search(expense_pattern, text, re.IGNORECASE)
        if expense_matches:
            expense_str = expense_matches.group(1).strip()
            expense_str = re.sub(r'[^\d.,]', '', expense_str).replace(',', '.')
            try:
                expenses = float(expense_str)
                
                # Check for unit multipliers
                if "tkr" in expense_matches.group(0) or "kkr" in expense_matches.group(0):
                    expenses *= 1000
                elif "mkr" in expense_matches.group(0):
                    expenses *= 1000000
                    
                page_extraction["income_statement.total_expenses"] = expenses
                page_extraction["confidence_scores"]["income_statement.total_expenses"] = 75
            except ValueError:
                pass
                
        # Pattern for property designation
        designation_pattern = r'(?:fastighetsbeteckning|fastighet)(?:en)?[^:]*?[:]\s*([^\n,;.]{3,50})'
        designation_matches = re.search(designation_pattern, text, re.IGNORECASE)
        if designation_matches:
            designation = designation_matches.group(1).strip()
            page_extraction["property_info.property_designation"] = designation
            page_extraction["confidence_scores"]["property_info.property_designation"] = 70
        
        # Simplified pattern for specific costs (focused on energy, heating, etc.)
        cost_categories = {
            "costs.energy_costs": [r'(?:el(?:kostnader|förbrukning|avgifter))[^\n]*?(\d[\d\s.,]*)'],
            "costs.heating_costs": [r'(?:värme(?:kostnader)?|uppvärmning)[^\n]*?(\d[\d\s.,]*)'],
            "costs.water_costs": [r'(?:vatten(?:kostnader|förbrukning)?)[^\n]*?(\d[\d\s.,]*)'],
            "costs.waste_management_costs": [r'(?:sophämtning|avfall(?:shantering)?)[^\n]*?(\d[\d\s.,]*)'],
            "costs.cleaning_costs": [r'(?:städ(?:ning)?|lokalvård)[^\n]*?(\d[\d\s.,]*)'],
            "costs.property_management_costs": [r'(?:fastighets(?:skötsel|förvaltning))[^\n]*?(\d[\d\s.,]*)'],
            "costs.insurance_costs": [r'(?:försäkring(?:skostnader)?)[^\n]*?(\d[\d\s.,]*)'],
            "costs.cable_tv_internet_costs": [r'(?:kabel-tv|bred(?:band)?|internet)[^\n]*?(\d[\d\s.,]*)'],
        }
        
        for cost_key, patterns in cost_categories.items():
            for pattern in patterns:
                cost_matches = re.search(pattern, text, re.IGNORECASE)
                if cost_matches:
                    cost_str = cost_matches.group(1).strip()
                    cost_str = re.sub(r'[^\d.,]', '', cost_str).replace(',', '.')
                    try:
                        cost_value = float(cost_str)
                        
                        # Check for unit multipliers
                        if "tkr" in cost_matches.group(0) or "kkr" in cost_matches.group(0):
                            cost_value *= 1000
                        elif "mkr" in cost_matches.group(0):
                            cost_value *= 1000000
                            
                        page_extraction[cost_key] = cost_value
                        page_extraction["confidence_scores"][cost_key] = 70
                    except ValueError:
                        pass
                        
        return page_extraction
    
    def _perform_vision_extraction(self, page_images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform vision-based extraction using Qwen VL Max
        
        Args:
            page_images: List of page image dictionaries
            
        Returns:
            Dictionary with vision extraction results
        """
        vision_results = {
            "costs": {},
            "property_info": {
                "property_designation": None,
                "total_area": None,
                "residential_area": None,
                "commercial_area": None,
                "apartment_count": None,
                "year_built": None,
                "tax_value": None
            },
            "income_statement": {
                "total_revenue": None,
                "total_expenses": None,
                "profit_loss": None,
                "operating_costs": {}
            },
            "balance_sheet": {
                "assets": {
                    "current_assets": None,
                    "fixed_assets": None,
                    "total_assets": None
                },
                "liabilities": {
                    "short_term_liabilities": None,
                    "long_term_liabilities": None,
                    "total_liabilities": None
                },
                "equity": None
            },
            "extraction_metadata": {
                "vision_extraction": True,
                "model": MODEL,
                "pages_processed": len(page_images),
                "extraction_timestamp": datetime.now().isoformat(),
                "filename": self.filename,
                "page_results": {}
            },
            "page_analyses": {}
        }
        
        # Process each page with vision API
        for page_data in tqdm(page_images, desc="Vision processing"):
            page_num = page_data["page_number"]
            img_base64 = page_data["base64"]
            
            # Extract information using vision API
            page_extraction = self._extract_info_from_image(img_base64, page_num)
            
            # Store page-specific results
            vision_results["extraction_metadata"]["page_results"][str(page_num)] = {
                "fields_extracted": list(page_extraction.keys())
            }
            
            # Store page analysis
            if "analysis" in page_extraction:
                vision_results["page_analyses"][str(page_num)] = page_extraction["analysis"]
                del page_extraction["analysis"]
            
            # Update main results with page extraction
            self._update_results_dict(vision_results, page_extraction)
        
        return vision_results
    
    def _extract_info_from_image(self, img_base64: str, page_num: int) -> Dict[str, Any]:
        """
        Extract information from image using vision API
        
        Args:
            img_base64: Base64-encoded image
            page_num: Page number
            
        Returns:
            Dictionary with extracted information
        """
        page_extraction = {
            "confidence_scores": {},
            "analysis": {}
        }
        
        # Create optimized prompt for Qwen VL Max
        prompt = """
        Du är en expert på svenska årsredovisningar för bostadsrättsföreningar.
        
        Analys av denna skannade sida från en BRF årsredovisning:
        
        1. Identifiera och extrahera följande EXAKTA finansiella och fastighetsdata:
           - Fastighetsbeteckning
           - Total area (kvadratmeter)
           - Bostadsyta (kvadratmeter)
           - Antal lägenheter
           - Byggår
           - Intäkter (årsavgifter, hyresintäkter)
           - Kostnader (uppvärmning, el, vatten, sophämtning, försäkring)
           - Resultat (årets resultat)
        
        2. För ALLA finansiella värden:
           - Extrahera det EXAKTA numeriska värdet
           - Ange enhet (tkr = tusen kronor, mkr = miljoner kronor)
           - Konvertera till standardformat (t.ex. "1 234 567,89 kr" till 1234567.89)
           - Kategorisera korrekt (kostnad, intäkt, tillgång, skuld)
        
        3. För fastighetsuppgifter:
           - Extrahera byggår EXAKT som presenterat
           - Extrahera total area och bostadsyta med korrekt enhet
           - Räkna det totala antalet lägenheter
        
        4. För tabelldata:
           - Identifiera kolumnrubriker
           - Extrahera rader med rätt värden
           - Behåll kolumn/rad-relationer
        
        Formatera ALL extraherad data i detta JSON-format:
        ```json
        {
          "property_info": {
            "property_designation": "Fastighetsnamn/beteckning",
            "total_area": 1234.5,
            "residential_area": 1000.0,
            "apartment_count": 42,
            "year_built": 1975
          },
          "income_statement": {
            "total_revenue": 1234567.0,
            "total_expenses": 1000000.0,
            "profit_loss": 234567.0
          },
          "costs": {
            "energy_costs": 123456.0,
            "heating_costs": 234567.0,
            "water_costs": 34567.0,
            "waste_management_costs": 23456.0,
            "cleaning_costs": 12345.0,
            "property_management_costs": 56789.0,
            "insurance_costs": 45678.0,
            "cable_tv_internet_costs": 34567.0
          },
          "confidence_scores": {
            "property_info.total_area": 95,
            "costs.heating_costs": 80
            // osv för varje extraherat värde
          }
        }
        ```
        
        VIKTIGT: Inkludera ENDAST faktiska värden från denna bild. Lämna fält som NULL om de inte finns i bilden.
        För värden du är osäker på, ange ett förtroendevärde (0-100) i confidence_scores.
        """
        
        # Prepare message with image
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            }
        ]
        
        try:
            # Call Vision API with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                    
                    payload = {
                        "model": MODEL,
                        "messages": messages,
                        "max_tokens": 4000,
                        "temperature": 0.1  # Low temperature for more deterministic results
                    }
                    
                    response = requests.post(
                        VISION_API_URL,
                        headers=headers,
                        json=payload,
                        timeout=60  # 60 second timeout
                    )
                    
                    if response.status_code == 200:
                        break
                    else:
                        logger.warning(f"Vision API request failed with status {response.status_code}: {response.text}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            
                except Exception as e:
                    logger.warning(f"Vision API request attempt {attempt+1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
            
            # Process API response
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Extract JSON from response
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Try to find JSON without markdown formatting
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = content
                
                try:
                    extraction = json.loads(json_str)
                    
                    # Store overall page analysis
                    before_json = content.split('```json')[0] if '```json' in content else ""
                    after_json = content.split('```')[-1] if '```' in content else ""
                    page_extraction["analysis"] = {
                        "before_json": before_json.strip(),
                        "after_json": after_json.strip(),
                        "api_status": response.status_code
                    }
                    
                    # Process extraction
                    if "property_info" in extraction:
                        for key, value in extraction["property_info"].items():
                            if value is not None and value != "":
                                field_key = f"property_info.{key}"
                                page_extraction[field_key] = value
                    
                    if "income_statement" in extraction:
                        for key, value in extraction["income_statement"].items():
                            if value is not None and value != "":
                                field_key = f"income_statement.{key}"
                                page_extraction[field_key] = value
                    
                    if "costs" in extraction:
                        for key, value in extraction["costs"].items():
                            if value is not None and value != "":
                                field_key = f"costs.{key}"
                                page_extraction[field_key] = value
                                
                    # Get confidence scores if available
                    if "confidence_scores" in extraction:
                        page_extraction["confidence_scores"] = extraction["confidence_scores"]
                    
                    # Set default confidence score for fields without explicit scores
                    for key in page_extraction:
                        if key != "confidence_scores" and key != "analysis":
                            if key not in page_extraction["confidence_scores"]:
                                page_extraction["confidence_scores"][key] = 75  # Default confidence
                                
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from vision API response for page {page_num}")
                    page_extraction["analysis"]["parse_error"] = True
            else:
                logger.error(f"Vision API request failed after {max_retries} attempts")
                page_extraction["analysis"]["api_error"] = f"Status code: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error extracting information from image: {str(e)}")
            page_extraction["analysis"]["error"] = str(e)
            
        return page_extraction
    
    def _update_results_dict(self, results: Dict[str, Any], extraction: Dict[str, Any]) -> None:
        """
        Update main results dictionary with new extraction data
        
        Args:
            results: Main results dictionary to update
            extraction: New extraction data
        """
        # Update confidence scores dictionary
        if "confidence_scores" in extraction:
            for field, score in extraction["confidence_scores"].items():
                self.confidence_scores[field] = score
        
        # Process all extracted fields
        for field, value in extraction.items():
            if field == "confidence_scores" or field == "analysis":
                continue
                
            # Skip None values
            if value is None:
                continue
                
            # Parse field path
            path_parts = field.split('.')
            
            # Handle nested fields
            current = results
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    # Last part - set the value
                    current[part] = value
                else:
                    # Intermediate path - ensure dictionary exists
                    if part not in current:
                        current[part] = {}
                    current = current[part]
    
    def _merge_results(self, ocr_results: Dict[str, Any], vision_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently merge OCR and vision results with confidence-based prioritization
        
        Args:
            ocr_results: Results from OCR extraction
            vision_results: Results from vision extraction
            
        Returns:
            Merged results dictionary
        """
        # Start with base structure
        merged = {
            "costs": {},
            "property_info": {
                "property_designation": None,
                "total_area": None,
                "residential_area": None,
                "commercial_area": None,
                "apartment_count": None,
                "year_built": None,
                "tax_value": None
            },
            "income_statement": {
                "total_revenue": None,
                "total_expenses": None,
                "profit_loss": None,
                "operating_costs": {},
                "financial_items": {},
                "comparison_year": None,
                "current_year": None
            },
            "balance_sheet": {
                "assets": {
                    "current_assets": None,
                    "fixed_assets": None,
                    "total_assets": None
                },
                "liabilities": {
                    "short_term_liabilities": None,
                    "long_term_liabilities": None,
                    "total_liabilities": None
                },
                "equity": None
            },
            "extraction_metadata": {
                "enhanced_tradgarden_extraction": True,
                "extraction_timestamp": datetime.now().isoformat(),
                "ocr_extraction_used": True,
                "vision_extraction_used": True,
                "ocr_language": self.ocr_lang,
                "ocr_dpi": self.dpi,
                "llm_model": MODEL,
                "filename": self.filename
            },
            "maintenance_info": {
                "historical_maintenance": [],
                "planned_maintenance": []
            }
        }
        
        # Merge fields from OCR and vision results based on confidence
        self._merge_field(merged, ocr_results, vision_results, ["property_info", "property_designation"])
        self._merge_field(merged, ocr_results, vision_results, ["property_info", "total_area"])
        self._merge_field(merged, ocr_results, vision_results, ["property_info", "residential_area"])
        self._merge_field(merged, ocr_results, vision_results, ["property_info", "commercial_area"])
        self._merge_field(merged, ocr_results, vision_results, ["property_info", "apartment_count"])
        self._merge_field(merged, ocr_results, vision_results, ["property_info", "year_built"])
        self._merge_field(merged, ocr_results, vision_results, ["property_info", "tax_value"])
        
        self._merge_field(merged, ocr_results, vision_results, ["income_statement", "total_revenue"])
        self._merge_field(merged, ocr_results, vision_results, ["income_statement", "total_expenses"])
        self._merge_field(merged, ocr_results, vision_results, ["income_statement", "profit_loss"])
        
        # Merge costs categories
        cost_categories = [
            "energy_costs", "heating_costs", "water_costs", "waste_management_costs",
            "cleaning_costs", "property_management_costs", "insurance_costs", 
            "cable_tv_internet_costs", "repair_costs", "maintenance_costs"
        ]
        
        for category in cost_categories:
            self._merge_field(merged, ocr_results, vision_results, ["costs", category])
        
        # Merge balance sheet fields
        self._merge_field(merged, ocr_results, vision_results, ["balance_sheet", "assets", "current_assets"])
        self._merge_field(merged, ocr_results, vision_results, ["balance_sheet", "assets", "fixed_assets"])
        self._merge_field(merged, ocr_results, vision_results, ["balance_sheet", "assets", "total_assets"])
        self._merge_field(merged, ocr_results, vision_results, ["balance_sheet", "liabilities", "short_term_liabilities"])
        self._merge_field(merged, ocr_results, vision_results, ["balance_sheet", "liabilities", "long_term_liabilities"])
        self._merge_field(merged, ocr_results, vision_results, ["balance_sheet", "liabilities", "total_liabilities"])
        self._merge_field(merged, ocr_results, vision_results, ["balance_sheet", "equity"])
        
        # Update metadata
        extracted_values = sum(1 for path, value in self._iterate_nested_dict(merged) 
                             if path[0] not in ["extraction_metadata", "maintenance_info"] and value is not None)
        
        merged["extraction_metadata"]["extracted_values_count"] = extracted_values
        
        # Calculate average confidence score
        confidence_scores = list(self.confidence_scores.values())
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            merged["extraction_metadata"]["average_confidence"] = round(avg_confidence, 2)
        else:
            merged["extraction_metadata"]["average_confidence"] = 0
            
        return merged
    
    def _merge_field(self, merged: Dict[str, Any], ocr_results: Dict[str, Any], 
                    vision_results: Dict[str, Any], field_path: List[str]) -> None:
        """
        Merge a specific field from OCR and vision results based on confidence
        
        Args:
            merged: Merged results dictionary to update
            ocr_results: OCR extraction results
            vision_results: Vision extraction results
            field_path: Path to the field in the dictionary
        """
        # Get values from OCR and vision results
        ocr_value = self._get_nested_value(ocr_results, field_path)
        vision_value = self._get_nested_value(vision_results, field_path)
        
        # Get confidence scores
        field_key = '.'.join(field_path)
        ocr_confidence = self.confidence_scores.get(f"ocr.{field_key}", 0)
        vision_confidence = self.confidence_scores.get(f"vision.{field_key}", 0)
        
        # Default confidence if not explicitly set
        if ocr_value is not None and ocr_confidence == 0:
            ocr_confidence = 70
        if vision_value is not None and vision_confidence == 0:
            vision_confidence = 80  # Slightly higher default for vision
            
        # Select value based on confidence and availability
        if ocr_value is None and vision_value is None:
            final_value = None
            final_confidence = 0
        elif ocr_value is None:
            final_value = vision_value
            final_confidence = vision_confidence
        elif vision_value is None:
            final_value = ocr_value
            final_confidence = ocr_confidence
        else:
            # Both values available, select based on confidence
            if ocr_confidence >= vision_confidence:
                final_value = ocr_value
                final_confidence = ocr_confidence
            else:
                final_value = vision_value
                final_confidence = vision_confidence
        
        # Update merged results
        if final_value is not None:
            self._set_nested_value(merged, field_path, final_value)
            self.confidence_scores[field_key] = final_confidence
    
    def _get_nested_value(self, d: Dict[str, Any], path: List[str]) -> Any:
        """
        Get value from nested dictionary
        
        Args:
            d: Dictionary to get value from
            path: Path to the value
            
        Returns:
            Value at the path, or None if not found
        """
        current = d
        for part in path:
            if part not in current:
                return None
            current = current[part]
        return current
    
    def _set_nested_value(self, d: Dict[str, Any], path: List[str], value: Any) -> None:
        """
        Set value in nested dictionary
        
        Args:
            d: Dictionary to set value in
            path: Path to the value
            value: Value to set
        """
        current = d
        for i, part in enumerate(path):
            if i == len(path) - 1:
                current[part] = value
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]
    
    def _iterate_nested_dict(self, d: Dict[str, Any], path: List[str] = None) -> List[Tuple[List[str], Any]]:
        """
        Iterate through all values in a nested dictionary
        
        Args:
            d: Dictionary to iterate
            path: Current path (used in recursion)
            
        Returns:
            List of (path, value) tuples
        """
        if path is None:
            path = []
            
        result = []
        
        for key, value in d.items():
            current_path = path + [key]
            
            if isinstance(value, dict):
                result.extend(self._iterate_nested_dict(value, current_path))
            else:
                result.append((current_path, value))
                
        return result
    
    def _post_process_results(self) -> None:
        """
        Apply post-processing to ensure consistency in the final results
        """
        # 1. Ensure operating costs match cost categories
        cost_categories = [
            "energy_costs", "heating_costs", "water_costs", "waste_management_costs",
            "cleaning_costs", "property_management_costs", "insurance_costs", 
            "cable_tv_internet_costs"
        ]
        
        for category in cost_categories:
            if category in self.combined_results["costs"] and self.combined_results["costs"][category] is not None:
                cost_value = self.combined_results["costs"][category]
                self.combined_results["income_statement"]["operating_costs"][category] = cost_value
        
        # 2. Calculate total expenses from operating costs if not extracted directly
        if (self.combined_results["income_statement"]["total_expenses"] is None and 
                self.combined_results["income_statement"]["operating_costs"]):
            
            operating_costs = sum(v for v in self.combined_results["income_statement"]["operating_costs"].values() 
                                if v is not None)
            
            if operating_costs > 0:
                self.combined_results["income_statement"]["total_expenses"] = operating_costs
                self.confidence_scores["income_statement.total_expenses"] = 60  # Lower confidence for derived value
        
        # 3. Calculate profit/loss if revenue and expenses are available
        if (self.combined_results["income_statement"]["profit_loss"] is None and
                self.combined_results["income_statement"]["total_revenue"] is not None and
                self.combined_results["income_statement"]["total_expenses"] is not None):
            
            revenue = self.combined_results["income_statement"]["total_revenue"]
            expenses = self.combined_results["income_statement"]["total_expenses"]
            
            profit_loss = revenue - expenses
            
            self.combined_results["income_statement"]["profit_loss"] = profit_loss
            self.confidence_scores["income_statement.profit_loss"] = 60  # Lower confidence for derived value
        
        # 4. Filter out low-confidence values
        for path, value in self._iterate_nested_dict(self.combined_results):
            field_key = '.'.join(path)
            confidence = self.confidence_scores.get(field_key, 0)
            
            if confidence < self.confidence_threshold:
                if path[0] not in ["extraction_metadata", "maintenance_info"]:
                    # Set to None if confidence is below threshold
                    self._set_nested_value(self.combined_results, path, None)
    
    def _print_extraction_summary(self) -> None:
        """
        Print a summary of the extraction results
        """
        # Count extracted values by category
        categories = {
            "property_info": 0,
            "income_statement": 0,
            "costs": 0,
            "balance_sheet": 0
        }
        
        for path, value in self._iterate_nested_dict(self.combined_results):
            if path[0] in categories and value is not None:
                categories[path[0]] += 1
        
        # Print summary
        print("\n======= EXTRACTION SUMMARY =======")
        print(f"Document: {self.filename}")
        print(f"Pages processed: {self.page_count}")
        print(f"Extraction timestamp: {self.combined_results['extraction_metadata']['extraction_timestamp']}")
        print("\nExtracted values by category:")
        for category, count in categories.items():
            print(f"  {category}: {count} values")
        
        print(f"\nTotal extracted values: {self.combined_results['extraction_metadata']['extracted_values_count']}")
        print(f"Average confidence score: {self.combined_results['extraction_metadata']['average_confidence']:.2f}")
        print("\nKey extracted information:")
        
        # Print key information if available
        if self.combined_results["property_info"]["total_area"]:
            print(f"  Total area: {self.combined_results['property_info']['total_area']} sqm")
        if self.combined_results["property_info"]["apartment_count"]:
            print(f"  Apartment count: {self.combined_results['property_info']['apartment_count']}")
        if self.combined_results["income_statement"]["total_revenue"]:
            print(f"  Total revenue: {self.combined_results['income_statement']['total_revenue']}")
        if self.combined_results["income_statement"]["total_expenses"]:
            print(f"  Total expenses: {self.combined_results['income_statement']['total_expenses']}")
            
        print("================================\n")


def main():
    """Main function for command line use"""
    parser = argparse.ArgumentParser(description="Enhanced OCR+Vision Processor for BRF Trädgården")
    parser.add_argument("--pdf", "-p", required=True, help="Path to PDF file")
    parser.add_argument("--output-dir", "-o", default=OUTPUT_DIR, help="Output directory")
    parser.add_argument("--api-key", "-k", help="API key for Qwen VL Max (uses .env if not provided)")
    parser.add_argument("--dpi", "-d", type=int, default=DPI, help="DPI for OCR preprocessing")
    parser.add_argument("--lang", "-l", default=OCR_LANGUAGE, help="Language for OCR")
    parser.add_argument("--confidence", "-c", type=int, default=CONFIDENCE_THRESHOLD, 
                      help="Minimum confidence threshold (0-100)")
    args = parser.parse_args()
    
    # Get API key from arguments or environment
    api_key = args.api_key or API_KEY
    if not api_key:
        print("Error: No API key provided. Please provide with --api-key or set DASHSCOPE_API_KEY in .env file.")
        return
    
    # Process the document
    processor = EnhancedTradgardenProcessor(
        pdf_path=args.pdf,
        api_key=api_key,
        output_dir=args.output_dir,
        dpi=args.dpi,
        ocr_lang=args.lang,
        confidence_threshold=args.confidence
    )
    
    results = processor.process()
    
    # Save final results
    output_path = os.path.join(args.output_dir, f"{os.path.basename(args.pdf)}_optimized_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Processing complete. Results saved to {output_path}")


if __name__ == "__main__":
    main()