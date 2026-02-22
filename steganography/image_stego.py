"""
Image Steganography Module

Supports hiding text data in images using LSB (Least Significant Bit) technique.
Supports PNG, BMP, and TIFF formats for lossless encoding.
"""

import numpy as np
import os
from PIL import Image
from typing import Optional, Tuple
from .utils import text_to_binary, binary_to_text, get_delimiter, encrypt_message, decrypt_message, bytes_to_binary, binary_to_bytes, encrypt_data, decrypt_data


class ImageSteganography:
    """Class for hiding and extracting data from images."""
    
    def __init__(self):
        self.delimiter = get_delimiter()
        self.supported_formats = ['.png', '.bmp', '.tiff', '.tif']
    
    def _get_capacity(self, image: Image.Image) -> int:
        """Calculate the maximum number of characters that can be hidden."""
        width, height = image.size
        channels = len(image.getbands())
        total_bits = width * height * channels
        # Account for delimiter
        usable_bits = total_bits - len(self.delimiter)
        return usable_bits // 8
    
    def get_image_info(self, image_path: str) -> dict:
        """Get information about an image file."""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.size[0],
                    'height': img.size[1],
                    'mode': img.mode,
                    'format': img.format,
                    'channels': len(img.getbands()),
                    'capacity': self._get_capacity(img)
                }
        except Exception as e:
            raise ValueError(f"Could not read image: {str(e)}")
    
    def hide_text(self, image_path: str, text: str, output_path: str, 
                  password: Optional[str] = None, callback=None, expiry_hours: float = 0) -> Tuple[bool, str]:
        """
        Hide text in an image using LSB steganography.
        
        Args:
            image_path: Path to the source image
            text: Text to hide
            output_path: Path to save the output image
            password: Optional password for encryption
            callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Load image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert image to numpy array
            img_array = np.array(img)
            original_shape = img_array.shape
            
            # Add expiration if requested
            if expiry_hours > 0:
                from .utils import add_expiration
                text = add_expiration(text, expiry_hours)

            # Prepare the message
            if password:
                text = encrypt_message(text, password)
            
            binary_text = text_to_binary(text) + self.delimiter
            
            # Check capacity
            total_pixels = img_array.size
            if len(binary_text) > total_pixels:
                return False, f"Text too large! Maximum {total_pixels // 8} characters allowed."
            
            # Flatten the array for easier manipulation
            flat_array = img_array.flatten()
            
            # Hide the data
            total_bits = len(binary_text)
            for i, bit in enumerate(binary_text):
                if callback and i % 10000 == 0:
                    callback(int((i / total_bits) * 100))
                # Modify the LSB
                flat_array[i] = (flat_array[i] & 0xFE) | int(bit)
            
            # Reshape and save
            stego_array = flat_array.reshape(original_shape)
            stego_img = Image.fromarray(stego_array.astype(np.uint8))
            
            # Ensure output is in lossless format
            if not output_path.lower().endswith(('.png', '.bmp', '.tiff', '.tif')):
                output_path += '.png'
            
            stego_img.save(output_path)
            
            if callback:
                callback(100)
            
            return True, f"Text hidden successfully in {output_path}"
            
        except Exception as e:
            return False, f"Error hiding text: {str(e)}"
    
    def extract_text(self, image_path: str, password: Optional[str] = None, 
                     callback=None, decoy_on_fail: bool = False, wipe_on_fail: bool = False) -> Tuple[bool, str]:
        """
        Extract hidden text from an image.
        
        Args:
            image_path: Path to the stego image
            password: Optional password for decryption
            callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success, message/extracted_text)
        """
        try:
            # Load image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_array = np.array(img)
            flat_array = img_array.flatten()
            
            # Extract LSBs
            binary_data = ''
            total_pixels = len(flat_array)
            
            for i, pixel in enumerate(flat_array):
                if callback and i % 10000 == 0:
                    callback(int((i / total_pixels) * 50))
                
                binary_data += str(pixel & 1)
                
                # Check for delimiter
                if binary_data.endswith(self.delimiter):
                    binary_data = binary_data[:-len(self.delimiter)]
                    break
            else:
                return False, "No hidden message found or message is corrupted."
            
            if callback:
                callback(75)
            
            # Convert binary to text
            extracted_text = binary_to_text(binary_data)
            
            # Decrypt if password provided
            # Decrypt if password provided
            if password:
                try:
                    extracted_text = decrypt_message(extracted_text, password)
                except ValueError as e:
                    # Security Features Trigger
                    from .utils import generate_decoy_message, wipe_file_data
                    
                    if wipe_on_fail:
                        wipe_file_data(image_path)
                        return False, "Security Triggered: Data has been wiped."
                    
                    if decoy_on_fail:
                        return True, generate_decoy_message()

                    return False, f"Decryption failed: {str(e)}"
            
            # Check for Expiration (Dead-Man Switch)
            from .utils import check_expiration, wipe_file_data
            is_expired, clean_text, has_header = check_expiration(extracted_text)
            
            if is_expired:
                wipe_file_data(image_path)
                return False, "⚠️ Dead-Man Switch Triggered: Message expired and self-destructed."
                
            if has_header:
                extracted_text = clean_text
            
            if callback:
                callback(100)
            
            return True, extracted_text
            
        except Exception as e:
            return False, f"Error extracting text: {str(e)}"
    
    def hide_image(self, cover_path: str, secret_path: str, output_path: str,
                   callback=None) -> Tuple[bool, str]:
        """
        Hide an image inside another image.
        
        Args:
            cover_path: Path to the cover image
            secret_path: Path to the secret image to hide
            output_path: Path to save the output
            callback: Optional callback function
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Load images
            cover = Image.open(cover_path).convert('RGB')
            secret = Image.open(secret_path).convert('RGB')
            
            # Resize secret to match cover
            secret = secret.resize(cover.size)
            
            cover_array = np.array(cover)
            secret_array = np.array(secret)
            
            # Use 4 MSBs from cover and 4 MSBs from secret
            stego_array = (cover_array & 0xF0) | (secret_array >> 4)
            
            stego_img = Image.fromarray(stego_array.astype(np.uint8))
            stego_img.save(output_path)
            
            if callback:
                callback(100)
            
            return True, f"Image hidden successfully in {output_path}"
            
        except Exception as e:
            return False, f"Error hiding image: {str(e)}"
    
    def extract_image(self, stego_path: str, output_path: str,
                      callback=None) -> Tuple[bool, str]:
        """
        Extract hidden image from a stego image.
        
        Args:
            stego_path: Path to the stego image
            output_path: Path to save the extracted image
            callback: Optional callback function
            
        Returns:
            Tuple of (success, message)
        """
        try:
            stego = Image.open(stego_path).convert('RGB')
            stego_array = np.array(stego)
            
            # Extract 4 LSBs and shift to MSB position
            extracted_array = (stego_array & 0x0F) << 4
            
            extracted_img = Image.fromarray(extracted_array.astype(np.uint8))
            extracted_img.save(output_path)
            
            if callback:
                callback(100)
            
            return True, f"Image extracted successfully to {output_path}"
            
        except Exception as e:
            return False, f"Error extracting image: {str(e)}"

    def hide_file(self, cover_path: str, file_path: str, output_path: str, 
                  password: Optional[str] = None, callback=None) -> Tuple[bool, str]:
        """Hide any file inside an image."""
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            
            filename = os.path.basename(file_path)
            
            if password:
                data = encrypt_data(data, password)
            
            # Header format: {{FILE:filename,SIZE:size}}
            header = f"{{{{FILE:{filename},SIZE:{len(data)}}}}}"
            full_binary = text_to_binary(header) + bytes_to_binary(data) + self.delimiter
            
            # Open cover
            img = Image.open(cover_path)
            img_array = np.array(img)
            total_pixels = img_array.size
            if len(full_binary) > total_pixels:
                 return False, f"File too large! Max {total_pixels // 8} bytes."

            # Flatten
            flat_array = img_array.flatten()
            
            # Hide
            for i, bit in enumerate(full_binary):
                if callback and i % 10000 == 0:
                     callback(int((i / len(full_binary)) * 100))
                flat_array[i] = (flat_array[i] & 0xFE) | int(bit)
                
            stego_array = flat_array.reshape(img_array.shape)
            stego_img = Image.fromarray(stego_array.astype(np.uint8))
            stego_img.save(output_path)
            
            if callback: callback(100)
            return True, f"File hidden in {output_path}"
        except Exception as e:
            return False, f"Error: {e}"

    def extract_file(self, stego_path: str, output_folder: str, 
                     password: Optional[str] = None, callback=None) -> Tuple[bool, str]:
        """Extract hidden file from stego image."""
        try:
            img = Image.open(stego_path)
            flat_array = np.array(img).flatten()
            
            # Read header first
            header_binary = ''
            header_found = False
            pixel_index = 0
            
            for i, pixel in enumerate(flat_array):
                header_binary += str(pixel & 1)
                pixel_index = i + 1
                if len(header_binary) % 8 == 0:
                    current_text = binary_to_text(header_binary)
                    if '}}' in current_text:
                        header_found = True
                        break
            
            if not header_found:
                return False, "No steganographic header found."
            
            # Parse header
            header_text = binary_to_text(header_binary)
            import re
            match = re.search(r"{{FILE:(.+?),SIZE:(\d+)}}", header_text)
            if not match:
                return False, "Invalid file header format."
            
            filename = match.group(1)
            filesize = int(match.group(2))
            
            # Read exact data bits
            data_bits_needed = filesize * 8
            if password:
                # Encryption adds padding/overhead. Fernet overhead is ~64-100 bytes.
                # Actually, our SIZE in header should be the size of 'data' BEFORE hiding, 
                # which is the encrypted data if password was used.
                pass

            data_binary = ''
            for i in range(pixel_index, pixel_index + data_bits_needed):
                if i >= len(flat_array):
                    break
                data_binary += str(flat_array[i] & 1)
                if callback and i % 50000 == 0:
                    callback(int(((i - pixel_index) / data_bits_needed) * 100))
            
            file_content = binary_to_bytes(data_binary)
            
            if password:
                try:
                    file_content = decrypt_data(file_content, password)
                except:
                    return False, "Incorrect Password"
            
            out_path = os.path.join(output_folder, filename)
            with open(out_path, 'wb') as f:
                f.write(file_content)
                
            if callback: callback(100)
            return True, f"Extracted to {out_path}"

        except Exception as e:
            return False, f"Error: {e}"
