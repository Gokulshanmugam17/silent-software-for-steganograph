
import os
import sys
import numpy as np
from PIL import Image

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from steganography.image_stego import ImageSteganography

def test_image_stego():
    print("Testing Image-in-Text Steganography (1-bit LSB)...")
    stego = ImageSteganography()
    img_path = "test_cover.png"
    out_path = "test_stego.png"
    data = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    Image.fromarray(data).save(img_path)
    secret_text = "Hello, this is a secret message!"
    password = "secure_password"
    success, msg = stego.hide_text(img_path, secret_text, out_path, password=password)
    if not success:
        print(f"Hide failed: {msg}")
        return
    success, extracted = stego.extract_text(out_path, password=password)
    if success and extracted == secret_text:
        print("✅ SUCCESS: Text matches!")
    else:
        print(f"❌ FAILURE: Extracted: {extracted}")
    if os.path.exists(img_path): os.remove(img_path)
    if os.path.exists(out_path): os.remove(out_path)

def test_image_in_image():
    print("\nTesting Image-in-Image Steganography (4-bit MSB)...")
    stego = ImageSteganography()
    cover_path = "test_cover_img.png"
    secret_path = "test_secret_img.png"
    out_path = "test_stego_img.png"
    ext_path = "test_extracted_img.png"
    cover_data = np.zeros((100, 100, 3), dtype=np.uint8)
    cover_data[:, :, 2] = 255 # Blue
    Image.fromarray(cover_data).save(cover_path)
    secret_data = np.zeros((100, 100, 3), dtype=np.uint8)
    secret_data[:, :, 0] = 255 # Red
    Image.fromarray(secret_data).save(secret_path)
    success, msg = stego.hide_image(cover_path, secret_path, out_path)
    if not success:
        print(f"Hide failed: {msg}")
        return
    success, msg = stego.extract_image(out_path, ext_path)
    if success:
        ext_img = np.array(Image.open(ext_path))
        print(f"Extracted Red sample pixel: {ext_img[0,0]}")
        if ext_img[0,0,0] >= 240:
            print("✅ SUCCESS: Image extracted successfully!")
        else:
            print("❌ FAILURE: Extracted colors are off.")
    else:
        print(f"❌ Extraction failed: {msg}")
    for p in [cover_path, secret_path, out_path, ext_path]:
        if os.path.exists(p): os.remove(p)

if __name__ == "__main__":
    test_image_stego()
    test_image_in_image()
