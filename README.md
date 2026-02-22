# SILENT - Secure Information Layering Engine

**SILENT** is a comprehensive, professional-grade steganography application that allows users to hide and extract secret data (text or files) within various carrier media (Text, Images, Audio, and Video) with built-in encryption and advanced security features.

## 🌟 Features

### Core Steganography
- **Text Steganography**: Zero-Width Character encoding (Unicode) to hide messages inside visible cover text
- **Image Steganography**: LSB (Least Significant Bit) substitution for PNG, BMP, and JPG formats
- **Audio Steganography**: LSB encoding for WAV files with perceptually unchanged audio quality
- **Video Steganography**: Frame-by-frame LSB encoding for AVI files using OpenCV

### Security Features
- **AES-256 Encryption**: All secret data encrypted with user-defined passwords
- **Dead-Man Switch**: Expiry timer where hidden data becomes inaccessible after a certain time
- **Decoy Mode**: Returns fake messages on wrong password to mislead forensic investigators
- **Self-Destruct**: Automatic data wiping on expiration or failed access attempts

### Advanced Features
- **Multi-Layer Steganography**: Recursive/nested hiding (e.g., text → image → audio → video)

### Interfaces
- **Web Interface**: Modern glassmorphism design with dark mode, drag-and-drop, and real-time previews
- **CLI Interface**: Command-line tool for power users and automation

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd newfolder11
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Web Interface

Launch the web application:
```bash
python main.py
```

The application will start on `http://127.0.0.1:8080` and automatically open in your browser.



### CLI Interface

#### Hide text in an image:
```bash
python cli.py hide image source.png output.png -t "Secret message" -p "password"
```

#### Extract text from an image:
```bash
python cli.py extract image stego.png -p "password"
```

#### Multi-layer steganography:
```bash
python cli.py multilayer hide --text "Secret" --layers image,video --covers cover.png,cover.avi --outputs layer1.png,layer2.avi
```

#### Get file information:
```bash
python cli.py info image image.png
```

## 📁 Project Structure

```
newfolder11/
├── steganography/          # Core steganography modules
│   ├── __init__.py
│   ├── text_stego.py       # Text steganography
│   ├── image_stego.py      # Image steganography
│   ├── audio_stego.py      # Audio steganography
│   ├── video_stego.py      # Video steganography
│   ├── multi_layer_stego.py # Multi-layer support
│   └── utils.py            # Utility functions
├── web_app/                # Flask web application
│   ├── app.py              # Flask routes and API
│   ├── templates/
│   │   └── index.html      # Web UI template
│   └── static/
│       ├── css/
│       │   └── style.css   # Glassmorphism styling
│       └── js/
│           └── main.js      # Frontend logic
├── main.py                 # Web app launcher

├── cli.py                  # Command-line interface
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🔐 Security Features Explained

### AES-256 Encryption
All secret data is encrypted using AES-256 before being hidden in the carrier media. The encryption key is derived from the user's password using PBKDF2 with 480,000 iterations.

### Dead-Man Switch
When hiding data, you can set an expiration time (in hours). After this time, any attempt to extract the data will trigger the dead-man switch, making the data inaccessible and optionally destroying it.

### Decoy Mode
If enabled, incorrect password attempts will return a believable fake message instead of an error, helping to mislead forensic investigators.

## 🎨 Web Interface Features

- **Dark Mode with Glassmorphism**: Modern, premium UI with glass-like effects
- **Purple/Indigo Accents**: Vibrant color scheme (#6366f1)
- **Space Grotesk Typography**: Modern, readable font
- **Drag-and-Drop**: Easy file uploads
- **Real-Time Preview**: Compare original vs. processed media
- **Toast Notifications**: Professional success/error messages
- **Progress Indicators**: Visual feedback for long operations



## 📝 Examples

### Example 1: Hide Text in Image
```python
from steganography.image_stego import ImageSteganography

stego = ImageSteganography()
success, message = stego.hide_text(
    "cover.png",
    "This is a secret message",
    "output.png",
    password="mypassword",
    expiry_hours=24
)
```

### Example 2: Extract with Decoy Mode
```python
success, result = stego.extract_text(
    "stego.png",
    password="wrongpassword",
    decoy_on_fail=True
)
# Returns fake message if password is wrong
```

### Example 3: Multi-Layer Hiding
```python
from steganography.multi_layer_stego import MultiLayerSteganography

ml_stego = MultiLayerSteganography()
layers = [
    {
        'type': 'image',
        'source': 'cover1.png',
        'output': 'layer1.png',
        'text': 'Secret message',
        'password': 'pass1'
    },
    {
        'type': 'audio',
        'source': 'cover2.wav',
        'output': 'layer2.wav',
        'password': 'pass2'
    }
]
success, msg = ml_stego.hide_layers(layers)
```

## ⚠️ Important Notes

1. **Lossless Formats**: For image steganography, always use lossless formats (PNG, BMP, TIFF) to preserve hidden data. JPEG compression will destroy the hidden information.

2. **Password Security**: Choose strong, unique passwords. The security of your hidden data depends on the password strength.

3. **File Size**: Larger carrier files can hide more data. Check capacity before hiding large files.

4. **Backup**: Always keep backups of your original files before processing.

5. **Legal Use**: This tool is for legitimate security and privacy purposes only. Use responsibly and in accordance with applicable laws.

## 🐛 Troubleshooting

### "Text too large" error
- Use a larger carrier file
- Reduce the size of the secret data
- Use multi-layer steganography for very large data

### "Decryption failed" error
- Verify the password is correct
- Check if the file was modified after hiding
- Ensure you're using the same encryption method

### Performance issues
- Large video files may take time to process
- Use progress callbacks to monitor status
- Consider using smaller carrier files for faster processing

## 📄 License

This project is provided as-is for educational and legitimate security purposes.

## 🤝 Contributing

Contributions are welcome! Please ensure all code follows the existing style and includes appropriate documentation.

## 📧 Support

For issues, questions, or feature requests, please open an issue on the repository.

---

**SILENT** - Secure Information Layering Engine for Non-Traceable Transmission

Version 1.0.0
