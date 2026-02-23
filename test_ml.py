
import os
import sys
import numpy as np
import cv2

# Add project root to path
root = "c:/Users/hhari/Desktop/SILENT-APP-main"
sys.path.insert(0, root)

from steganography.multi_layer_stego import MultiLayerSteganography

def test_multilayer():
    ml = MultiLayerSteganography()
    
    upload_dir = os.path.join(root, "web_app", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create test images
    img1_path = os.path.join(upload_dir, "test_cover1.png")
    img2_path = os.path.join(upload_dir, "test_cover2.png")
    
    cv2.imwrite(img1_path, np.zeros((100, 100, 3), dtype=np.uint8))
    cv2.imwrite(img2_path, np.zeros((200, 200, 3), dtype=np.uint8))
    
    out1 = os.path.join(upload_dir, "test_ml_out1.png")
    out2 = os.path.join(upload_dir, "test_ml_out2.png")
    
    layers = [
        {
            'type': 'image',
            'source': img1_path,
            'output': out1,
            'text': 'Secret level 1',
            'password': 'pass1'
        },
        {
            'type': 'image',
            'source': img2_path,
            'output': out2,
            'password': 'pass2'
        }
    ]
    
    print("Starting hide_layers...")
    success, msg = ml.hide_layers(layers)
    print(f"Success: {success}, Message: {msg}")

if __name__ == "__main__":
    test_multilayer()
