#!/usr/bin/env python3
"""
Test LayoutParser with Table-Specific Detectron2 Models
"""

import cv2
import numpy as np
from PIL import Image
import layoutparser as lp
from pathlib import Path

def test_layoutparser_table_detection(image_path: str):
    """Test LayoutParser with table-specific models"""
    
    print(f"🏗️ Testing LayoutParser Table Detection on: {Path(image_path).name}")
    
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not load image: {image_path}")
            return None
            
        pil_image = Image.open(image_path)
        height, width = image.shape[:2]
        print(f"📐 Image size: {width}x{height}")
        
        # Test different table-specific models
        models_to_test = [
            {
                "name": "PubLayNet (Table Focused)",
                "config": "lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
                "model": "lp://PubLayNet/faster_rcnn_R_50_FPN_3x/model_final.pth",
                "label_map": {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            },
            {
                "name": "TableBank (Table Specialist)", 
                "config": "lp://TableBank/faster_rcnn_R_50_FPN_3x/config",
                "model": "lp://TableBank/faster_rcnn_R_50_FPN_3x/model_final.pth",
                "label_map": {0: "Table"}
            }
        ]
        
        results = {}
        
        for model_info in models_to_test:
            print(f"\n🎯 Testing: {model_info['name']}")
            
            try:
                # Create model
                model = lp.Detectron2LayoutModel(
                    config_path=model_info["config"],
                    model_path=model_info["model"],
                    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.6],
                    label_map=model_info["label_map"]
                )
                
                print("✅ Model loaded successfully")
                
                # Run detection
                layout = model.detect(pil_image)
                print(f"✅ Detection completed: {len(layout)} objects found")
                
                # Filter for tables only
                tables = [block for block in layout if block.type == "Table"]
                print(f"🏆 Tables found: {len(tables)}")
                
                if tables:
                    for i, table in enumerate(tables):
                        bbox = table.block
                        confidence = table.score
                        area = bbox.width * bbox.height
                        
                        print(f"   📋 Table {i+1}:")
                        print(f"      BBox: [{bbox.x_1:.0f}, {bbox.y_1:.0f}, {bbox.x_2:.0f}, {bbox.y_2:.0f}]")
                        print(f"      Score: {confidence:.3f}")
                        print(f"      Area: {area:.0f}")
                        
                        # Save the best table for this model
                        if i == 0:  # Save the first/best table
                            results[model_info['name']] = {
                                "tables_found": len(tables),
                                "best_table": {
                                    "bbox": [bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2],
                                    "confidence": confidence,
                                    "area": area
                                }
                            }
                else:
                    print("   ❌ No tables detected")
                    results[model_info['name']] = {"tables_found": 0, "best_table": None}
                    
            except Exception as e:
                print(f"   ❌ Error with {model_info['name']}: {e}")
                results[model_info['name']] = {"error": str(e)}
        
        return results
        
    except Exception as e:
        print(f"❌ General error: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_best_layoutparser_table(image_path: str, output_dir: str = "layoutparser_output"):
    """Extract the best table using LayoutParser"""
    
    results = test_layoutparser_table_detection(image_path)
    
    if not results:
        return None
    
    # Find the best result
    best_model = None
    best_table = None
    max_tables = 0
    
    for model_name, result in results.items():
        if "error" not in result and result["tables_found"] > max_tables:
            max_tables = result["tables_found"] 
            best_model = model_name
            best_table = result["best_table"]
    
    if best_table:
        print(f"\n🏆 BEST LAYOUTPARSER RESULT: {best_model}")
        print(f"   Tables found: {max_tables}")
        print(f"   Best table confidence: {best_table['confidence']:.3f}")
        
        # Extract and save the best table
        image = cv2.imread(image_path)
        x1, y1, x2, y2 = [int(coord) for coord in best_table["bbox"]]
        
        # Add padding
        padding = 20
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding) 
        x2 = min(image.shape[1], x2 + padding)
        y2 = min(image.shape[0], y2 + padding)
        
        cropped = image[y1:y2, x1:x2]
        
        # Save
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        filename = f"layoutparser_table_{Path(image_path).stem}.jpg"
        save_path = output_path / filename
        cv2.imwrite(str(save_path), cropped)
        
        print(f"✅ Table saved: {save_path}")
        
        return {
            "method": "LayoutParser",
            "model": best_model,
            "bbox": best_table["bbox"],
            "confidence": best_table["confidence"],
            "area": best_table["area"],
            "output_path": str(save_path)
        }
    
    else:
        print("❌ No tables found by any LayoutParser model")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_layoutparser_tables.py <image.jpg>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    result = extract_best_layoutparser_table(image_path)
    
    if result:
        print(f"\n🎉 SUCCESS! LayoutParser table detection working!")
    else:
        print(f"\n❌ No tables detected by LayoutParser")