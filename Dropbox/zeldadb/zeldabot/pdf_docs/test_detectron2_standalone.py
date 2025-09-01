#!/usr/bin/env python3
"""
Standalone Detectron2 Test for Table Detection
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path

def test_detectron2_table_detection(image_path: str):
    """Test Detectron2 table detection standalone"""
    
    print(f"🔍 Testing Detectron2 on: {image_path}")
    
    try:
        import detectron2
        from detectron2 import model_zoo
        from detectron2.engine import DefaultPredictor
        from detectron2.config import get_cfg
        
        print("✅ Detectron2 imports successful")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not load image: {image_path}")
            return
        
        height, width = image.shape[:2]
        print(f"📐 Image size: {width}x{height}")
        
        # Setup Detectron2 config
        cfg = get_cfg()
        cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
        cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml")
        cfg.MODEL.DEVICE = "cpu"  # Force CPU usage
        
        print("✅ Config setup successful")
        
        # Create predictor
        predictor = DefaultPredictor(cfg)
        print("✅ Predictor created")
        
        # Run detection
        outputs = predictor(image)
        print("✅ Prediction completed")
        
        # Get results
        instances = outputs["instances"]
        num_detections = len(instances)
        
        print(f"🎯 Detectron2 found: {num_detections} objects")
        
        if num_detections > 0:
            boxes = instances.pred_boxes.tensor.cpu().numpy()
            scores = instances.scores.cpu().numpy()
            classes = instances.pred_classes.cpu().numpy()
            
            for i in range(min(5, num_detections)):  # Show top 5
                x1, y1, x2, y2 = boxes[i]
                score = scores[i]
                class_id = classes[i]
                
                area = (x2 - x1) * (y2 - y1)
                print(f"   Object {i+1}: Class={class_id}, Score={score:.2f}, Area={area:.0f}")
                print(f"             BBox=[{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]")
        
        # Find largest detection (most likely to be a table)
        if num_detections > 0:
            areas = [(b[2]-b[0])*(b[3]-b[1]) for b in boxes]
            best_idx = np.argmax(areas)
            
            best_box = boxes[best_idx]
            best_score = scores[best_idx]
            best_area = areas[best_idx]
            
            print(f"\n🏆 LARGEST DETECTION:")
            print(f"   BBox: [{best_box[0]:.0f}, {best_box[1]:.0f}, {best_box[2]:.0f}, {best_box[3]:.0f}]")
            print(f"   Score: {best_score:.2f}")
            print(f"   Area: {best_area:.0f}")
            
            return {
                "method": "detectron2",
                "bbox": best_box.tolist(),
                "confidence": float(best_score),
                "area": float(best_area)
            }
        else:
            print("❌ No objects detected")
            return None
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_detectron2_standalone.py <image.jpg>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    result = test_detectron2_table_detection(image_path)
    
    if result:
        print(f"\n✅ SUCCESS: Detectron2 working properly!")
        print(f"   Method: {result['method']}")
        print(f"   Confidence: {result['confidence']:.2f}")
    else:
        print(f"\n❌ FAILED: Detectron2 not working")