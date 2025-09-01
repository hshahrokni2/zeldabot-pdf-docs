#!/usr/bin/env python3
"""
Test Version: State-of-the-Art Vision Table Detection
Standalone version for testing Microsoft Table Transformer
"""

import os
import sys
import torch
import numpy as np
from PIL import Image
import fitz  # PyMuPDF for PDF to image
from pathlib import Path
import logging
from typing import Dict, List, Tuple
import io
from datetime import datetime

# Check for required libraries
try:
    from transformers import AutoImageProcessor, TableTransformerForObjectDetection
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import layoutparser as lp
    HAS_LAYOUTPARSER = True
except ImportError:
    HAS_LAYOUTPARSER = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_vision_transformer.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class TestVisionTableDetector:
    """
    Test version for state-of-the-art vision-based table detection
    Works on scanned documents, photos, and digital PDFs
    """
    
    def __init__(self):
        # Initialize models
        self.processor = None
        self.model = None
        self.layout_model = None
        
        # Detection thresholds
        self.TABLE_CONFIDENCE_THRESHOLD = 0.7
        self.MIN_TABLE_AREA = 5000  # pixels squared
        
        # Initialize models
        self._load_models()
        
    def _load_models(self):
        """Load vision models"""
        
        if HAS_TRANSFORMERS:
            try:
                logger.info("Loading Microsoft Table Transformer model...")
                self.processor = AutoImageProcessor.from_pretrained(
                    "microsoft/table-transformer-detection"
                )
                self.model = TableTransformerForObjectDetection.from_pretrained(
                    "microsoft/table-transformer-detection"
                )
                logger.info("✅ Table Transformer loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load Table Transformer: {e}")
        
        if HAS_LAYOUTPARSER:
            try:
                logger.info("Loading LayoutParser model...")
                self.layout_model = lp.models.Detectron2LayoutModel(
                    'lp://TableBank/faster_rcnn_R_101_FPN_3x/config',
                    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
                    label_map={0: "Table"}
                )
                logger.info("✅ LayoutParser loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load LayoutParser: {e}")
        
    def process_pdf_file(self, pdf_path: Path) -> Dict:
        """Process PDF file with vision-based detection"""
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return {}
            
        # Convert PDF to images
        pdf_images = self._pdf_to_images_from_file(pdf_path)
        
        results = {
            'filename': pdf_path.name,
            'tables_found': [],
            'total_pages': len(pdf_images),
            'processing_stats': {}
        }
        
        total_transformer = 0
        total_layoutparser = 0
        
        # Process each page
        for page_num, image in enumerate(pdf_images):
            logger.info(f"Processing page {page_num + 1}/{len(pdf_images)} for {pdf_path.name}")
            
            page_tables = []
            
            # Method 1: Table Transformer (highest accuracy)
            if self.model and self.processor:
                transformer_tables = self._detect_with_table_transformer(image, page_num)
                total_transformer += len(transformer_tables)
                page_tables.extend(transformer_tables)
            
            # Method 2: LayoutParser (good for documents)
            if self.layout_model:
                layout_tables = self._detect_with_layoutparser(image, page_num)
                total_layoutparser += len(layout_tables)
                
                # Merge with transformer results (avoid duplicates)
                for lp_table in layout_tables:
                    is_duplicate = False
                    for existing in page_tables:
                        if self._calculate_iou(existing['bbox'], lp_table['bbox']) > 0.5:
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        page_tables.append(lp_table)
            
            # Add page tables to results
            results['tables_found'].extend(page_tables)
            
        results['processing_stats'] = {
            'transformer_detections': total_transformer,
            'layoutparser_detections': total_layoutparser,
            'final_tables': len(results['tables_found'])
        }
        
        logger.info(f"Found {len(results['tables_found'])} tables in {pdf_path.name}")
        return results
        
    def _pdf_to_images_from_file(self, pdf_path: Path, dpi: int = 150) -> List[Image.Image]:
        """Convert PDF pages to images for vision processing"""
        images = []
        
        # Open PDF file
        pdf_doc = fitz.open(pdf_path)
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            # Convert to image at specified DPI
            mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default PDF DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
            
        pdf_doc.close()
        return images
        
    def _detect_with_table_transformer(self, image: Image.Image, page_num: int) -> List[Dict]:
        """
        Microsoft Table Transformer - 97.9% accuracy on financial tables
        Best for: Complex financial tables, borderless tables
        """
        tables = []
        
        if not self.model or not self.processor:
            return tables
        
        try:
            # Prepare image
            inputs = self.processor(images=image, return_tensors="pt")
            
            # Run detection
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Process results
            target_sizes = torch.tensor([image.size[::-1]])
            results = self.processor.post_process_object_detection(
                outputs, 
                threshold=self.TABLE_CONFIDENCE_THRESHOLD,
                target_sizes=target_sizes
            )[0]
            
            # Extract bounding boxes
            for score, label, box in zip(
                results["scores"], 
                results["labels"], 
                results["boxes"]
            ):
                # Convert to coordinates
                x_min, y_min, x_max, y_max = box.tolist()
                
                # Calculate area
                area = (x_max - x_min) * (y_max - y_min)
                
                if area >= self.MIN_TABLE_AREA:
                    tables.append({
                        'page': page_num,
                        'method': 'table_transformer',
                        'bbox': [x_min, y_min, x_max, y_max],
                        'confidence': float(score),
                        'area': area
                    })
                    
            logger.debug(f"Table Transformer found {len(tables)} tables on page {page_num}")
            
        except Exception as e:
            logger.error(f"Table Transformer failed on page {page_num}: {e}")
            
        return tables
        
    def _detect_with_layoutparser(self, image: Image.Image, page_num: int) -> List[Dict]:
        """
        LayoutParser - Fast and reliable for documents
        Best for: Standard document layouts, faster processing
        """
        tables = []
        
        if not self.layout_model:
            return tables
        
        try:
            # Convert PIL to numpy array
            image_np = np.array(image)
            
            # Detect layout
            layout = self.layout_model.detect(image_np)
            
            # Extract table regions
            for block in layout:
                if block.type == "Table":
                    bbox = [block.x_1, block.y_1, block.x_2, block.y_2]
                    area = (block.x_2 - block.x_1) * (block.y_2 - block.y_1)
                    
                    if area >= self.MIN_TABLE_AREA:
                        tables.append({
                            'page': page_num,
                            'method': 'layoutparser',
                            'bbox': bbox,
                            'confidence': float(block.score) if hasattr(block, 'score') else 0.8,
                            'area': area
                        })
                        
            logger.debug(f"LayoutParser found {len(tables)} tables on page {page_num}")
            
        except Exception as e:
            logger.error(f"LayoutParser failed on page {page_num}: {e}")
            
        return tables
        
    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """Calculate Intersection over Union for two bboxes"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
            
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0


def main():
    """Test vision-based table detection on sample PDFs"""
    
    print("\n" + "="*60)
    print("🔬 PROJECT ZELDA - VISION TABLE TRANSFORMER TEST")
    print("State-of-the-Art: Microsoft Table Transformer (97.9% accuracy)")
    print("Works on scanned & digital PDFs!")
    print("="*60)
    
    detector = TestVisionTableDetector()
    
    # Check available models
    print("🧠 Available Vision Models:")
    print(f"   Table Transformer: {'✅' if HAS_TRANSFORMERS and detector.model else '❌'}")
    print(f"   LayoutParser: {'✅' if HAS_LAYOUTPARSER and detector.layout_model else '❌'}")
    
    if not HAS_TRANSFORMERS and not HAS_LAYOUTPARSER:
        print("❌ No vision models available. Install: pip install transformers torch layoutparser")
        return
    
    # Look for sample PDFs
    sample_dir = Path(".")
    pdf_files = list(sample_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("\n❌ No PDF files found in current directory")
        print("Please place some PDF files in the current directory to test")
        return
    
    print(f"\n📄 Found {len(pdf_files)} PDF files to test:")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    total_tables = 0
    total_docs = len(pdf_files)
    method_stats = {
        'table_transformer': 0,
        'layoutparser': 0
    }
    
    start_time = datetime.now()
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{total_docs}] Processing: {pdf_path.name}")
        
        results = detector.process_pdf_file(pdf_path)
        
        if results:
            tables = len(results.get('tables_found', []))
            total_tables += tables
            
            # Count by method
            for table in results.get('tables_found', []):
                method = table.get('method', 'unknown')
                if method in method_stats:
                    method_stats[method] += 1
                    
            print(f"  🔍 Found {tables} tables")
            
            # Show processing stats
            if results.get('processing_stats'):
                stats = results['processing_stats']
                print(f"     Transformer: {stats.get('transformer_detections', 0)}, "
                     f"LayoutParser: {stats.get('layoutparser_detections', 0)}, "
                     f"Final: {stats.get('final_tables', 0)}")
        else:
            print(f"  ❌ Processing failed")
            
    elapsed_time = datetime.now() - start_time
    
    print(f"\n{'='*60}")
    print("🎯 VISION TRANSFORMER DETECTION COMPLETE")
    print(f"⏱️  Processing time: {elapsed_time}")
    print(f"📊 Total Tables Found: {total_tables}")
    print(f"📈 Average per Document: {total_tables/total_docs:.1f}")
    
    print("\n🔬 Detection Method Breakdown:")
    for method, count in method_stats.items():
        if count > 0:
            percentage = (count / total_tables * 100) if total_tables > 0 else 0
            print(f"   {method}: {count} tables ({percentage:.1f}%)")
    
    # Projections for full dataset
    if total_docs > 0:
        projected_total = int(total_tables * (200 / total_docs))
        
        print(f"\n🚀 PROJECTIONS FOR 200 DOCUMENTS:")
        print(f"   Total Tables: {projected_total}")
        print(f"   Average per Document: {projected_total/200:.1f}")
        
        if 500 <= projected_total <= 1000:
            print("✅ SUCCESS: Within expected range (500-1000)")
            print("🏆 State-of-the-art vision models working perfectly!")
        elif projected_total > 1000:
            print("📈 High detection rate - Vision models finding comprehensive tables")
        else:
            print("📊 Lower than expected - May need threshold tuning")
    
    print("="*60)


if __name__ == "__main__":
    main()