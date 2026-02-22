
import sys
import os

# Add the project root to sys.path
root_dir = os.path.abspath(os.curdir)
sys.path.insert(0, root_dir)

modules_to_test = [
    'steganography.utils',
    'steganography.image_stego',
    'steganography.audio_stego',
    'steganography.video_stego',
    'steganography.text_stego',
    'steganography.multi_layer_stego',
    'web_app.app'
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"SUCCESS: Imported {module_name}")
    except Exception as e:
        print(f"FAILED:  Importing {module_name}: {e}")
        import traceback
        traceback.print_exc()
