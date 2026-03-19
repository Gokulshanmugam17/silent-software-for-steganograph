import sys
import os
sys.path.insert(0, r"c:\Users\hhari\Desktop\SILENT-APP")
from steganography.image_stego import ImageSteganography
from PIL import Image
import numpy as np

stego = ImageSteganography()
img = Image.new('RGB', (100, 100), color = 'red')
img.save('test_cover_2.png')

print("Hiding 'oooo'...")
success, msg = stego.hide_text('test_cover_2.png', 'oooo', 'test_stego_2.png', password='')
print(f"Hide: {success}, {msg}")

print("Extracting 'oooo'...")
success, msg = stego.extract_text('test_stego_2.png', password='')
print(f"Extract: {success}, {msg}")
