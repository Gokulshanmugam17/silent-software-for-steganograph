import sys
import os
sys.path.insert(0, r"c:\Users\hhari\Desktop\SILENT-APP")
from steganography.image_stego import ImageSteganography
from PIL import Image
import numpy as np

stego = ImageSteganography()
# create dummy image
img = Image.new('RGB', (100, 100), color = 'red')
img.save('test_cover.png')

print("Hiding text...")
success, msg = stego.hide_text('test_cover.png', 'Hello World', 'test_stego.png', password='test')
print(f"Hide result: {success}, {msg}")

print("Extracting text...")
success, msg = stego.extract_text('test_stego.png', password='test')
print(f"Extract result: {success}, {msg}")

if not success:
    # let's find out why
    img = Image.open('test_stego.png')
    flat_array = np.array(img).flatten()
    lsbs = (flat_array & 1).astype(np.uint8)
    delimiter_bits = np.array([int(b) for b in stego.delimiter], dtype=np.uint8)
    
    lsbs_packed = np.packbits(lsbs)
    del_packed = np.packbits(delimiter_bits)
    
    idx = lsbs_packed.tobytes().find(del_packed.tobytes())
    print(f"Packed find idx: {idx}")
    
    # Try sliding window finding
    idx2 = -1
    for i in range(len(lsbs) - len(delimiter_bits) + 1):
        if np.array_equal(lsbs[i : i + len(delimiter_bits)], delimiter_bits):
            idx2 = i
            break
    print(f"Sliding window idx: {idx2}")
