import sys
import os
sys.path.insert(0, r"c:\Users\hhari\Desktop\SILENT-APP")
from web_app.app import app
from PIL import Image
from io import BytesIO

# create dummy image
img = Image.new('RGB', (100, 100), color = 'red')
img_byte_arr = BytesIO()
img.save(img_byte_arr, format='PNG')
img_byte_arr.seek(0)

# create test client
client = app.test_client()

# 1. HIDE TEXT
data = {
    'operation': 'hide',
    'media_type': 'image',
    'data_type': 'text',
    'text_data': 'oooo',
    'password': '',
    'source_file': (img_byte_arr, 'test_cover.png')
}
res = client.post('/process', data=data, content_type='multipart/form-data')
print("HIDE RESPONSE:", res.json)
stego_url = res.json.get('download_url')
print("Stego URL:", stego_url)

# The file is saved in uploads dir
filename = os.path.basename(stego_url)
filepath = os.path.join(r"c:\Users\hhari\Desktop\SILENT-APP\web_app\uploads", filename)

# 2. EXTRACT TEXT
with open(filepath, 'rb') as f:
    stego_data = f.read()

data_ext = {
    'operation': 'extract',
    'media_type': 'image',
    'data_type': 'text',
    'password': '',
    'source_file': (BytesIO(stego_data), filename)
}

res_ext = client.post('/process', data=data_ext, content_type='multipart/form-data')
print("EXTRACT RESPONSE:", res_ext.json)
