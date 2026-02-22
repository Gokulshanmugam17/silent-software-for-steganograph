"""
Utility functions for steganography operations.
"""

import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Tuple


def text_to_binary(text: str) -> str:
    """Convert text to binary string."""
    return ''.join(format(ord(char), '08b') for char in text)

def bytes_to_binary(data: bytes) -> str:
    """Convert bytes to binary string."""
    return ''.join(format(byte, '08b') for byte in data)

def binary_to_bytes(binary: str) -> bytes:
    """Convert binary string to bytes."""
    binary_values = [binary[i:i+8] for i in range(0, len(binary), 8)]
    # Filter out incomplete bytes
    binary_values = [b for b in binary_values if len(b) == 8]
    return bytes([int(b, 2) for b in binary_values])

def binary_to_text(binary: str) -> str:
    """Convert binary string to text."""
    try:
        bytes_data = binary_to_bytes(binary)
        return bytes_data.decode('utf-8')
    except Exception:
        # Fallback for corrupted data: try to interpret as characters safely
        chars = []
        for i in range(0, len(binary), 8):
            byte_str = binary[i:i+8]
            if len(byte_str) == 8:
                val = int(byte_str, 2)
                # Filter out obvious non-printable/control characters if it's supposed to be text
                if 32 <= val <= 126 or val > 160:
                    chars.append(chr(val))
        return ''.join(chars)


def get_delimiter() -> str:
    """
    Get the end-of-message delimiter in binary.
    Using 'SILENT_DONE' in binary (80 bits) to avoid accidental collisions.
    """
    return '0101001101001001010011000100010101001110010101000101111101000100010011110100111001000101'


def generate_key(password: str) -> bytes:
    """Generate encryption key from password."""
    salt = b'steganography_salt_v1'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_message(message: str, password: str) -> str:
    """Encrypt a message using password."""
    key = generate_key(password)
    f = Fernet(key)
    encrypted = f.encrypt(message.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_message(encrypted_message: str, password: str) -> str:
    """Decrypt a message using password."""
    try:
        key = generate_key(password)
        f = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

def encrypt_data(data: bytes, password: str) -> bytes:
    """Encrypt raw bytes."""
    key = generate_key(password)
    f = Fernet(key)
    return f.encrypt(data)

def decrypt_data(data: bytes, password: str) -> bytes:
    """Decrypt raw bytes."""
    try:
        key = generate_key(password)
        f = Fernet(key)
        return f.decrypt(data)
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

def generate_decoy_message() -> str:
    """Generate a believable fake message."""
    decoys = [
        "Meeting confirmed for Tuesday at 2 PM.",
        "The project deadline has been extended.",
        "Please send the logs by EOD.",
        "Error: Log file corrupted. Code: 404.",
        "Coordinates: 34.0522° N, 118.2437° W",
        "Recipe: 2 cups flour, 1 cup sugar, 2 eggs.",
        "Account ID: 8832-1192-4432 (Inactive)",
        "System update scheduled for midnight."
    ]
    import random
    return random.choice(decoys)

def wipe_file_data(file_path: str):
    """
    Corrupts the data in the file to destroy hidden information.
    For images/audio, this adds noise to LSBs.
    For simplicity and speed, we will overwrite the file with random binary data 
    if it's a copy, or just noise injection.
    
    WARNING: This is destructive.
    """
    try:
        import os
        import random
        # We don't want to delete the file, just ruin the data.
        # But steganography is in LSB. 
        # A simple approach for self-destruct is to overwrite the file 
        # with random bytes if it allows, OR just report it's wiped.
        # Since we want to assume the attacker has the file, 
        # we can only wipe it if we have write access to that file path.
        
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb+') as f:
            # Overwrite random chunks to corrupt LSBs specifically?
            # Or just overwrite the whole thing with noise which destroys the file structure?
            # Destroying file structure makes it obvious. 
            # Ideally we want to keep the image looking valid but empty the LSBs.
            # But that is complex to implement generically.
            
            # "Scorched Earth": Overwrite with random data
            f.seek(0)
            f.write(os.urandom(file_size))
            
    except Exception as e:
        print(f"Wipe failed: {e}")

def add_expiration(text: str, hours: float) -> str:
    """Add expiration timestamp header to text."""
    import time
    # Calculate expiry timestamp
    expiry = time.time() + (hours * 3600)
    # Header format: {{EXP:1234567890.12}}
    return f"{{{{EXP:{expiry:.2f}}}}}{text}"

def check_expiration(text: str) -> Tuple[bool, str, bool]:
    """
    Check if text has expiration header and if it's expired.
    Returns: (is_expired, clean_text, has_header)
    """
    import time
    import re
    
    # Check for header
    match = re.match(r"^\{\{EXP:(\d+\.?\d*)\}\}(.*)", text, re.DOTALL)
    if not match:
        return False, text, False
        
    expiry_timestamp = float(match.group(1))
    clean_text = match.group(2)
    
    if time.time() > expiry_timestamp:
        return True, clean_text, True
        
    return False, clean_text, True

def calculate_capacity(file_size: int, bits_per_unit: int = 1) -> int:
    """Calculate the capacity in characters for hiding data."""
    return (file_size * bits_per_unit) // 8


def file_to_binary(file_path: str) -> str:
    """Convert file contents to binary string."""
    with open(file_path, 'rb') as f:
        data = f.read()
    return ''.join(format(byte, '08b') for byte in data)


def binary_to_file(binary: str, output_path: str):
    """Convert binary string back to file."""
    bytes_data = bytes(int(binary[i:i+8], 2) for i in range(0, len(binary), 8))
    with open(output_path, 'wb') as f:
        f.write(bytes_data)


def get_file_extension(file_path: str) -> str:
    """Get file extension."""
    return os.path.splitext(file_path)[1].lower()


def validate_image_format(file_path: str) -> bool:
    """Validate if file is a supported image format."""
    supported = ['.png', '.bmp', '.tiff', '.tif']
    return get_file_extension(file_path) in supported


def validate_audio_format(file_path: str) -> bool:
    """Validate if file is a supported audio format."""
    supported = ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.mpeg', '.aac', '.wma', '.aiff']
    return get_file_extension(file_path) in supported


def validate_video_format(file_path: str) -> bool:
    """Validate if file is a supported video format."""
    supported = ['.avi', '.mp4', '.mkv']
    return get_file_extension(file_path) in supported
