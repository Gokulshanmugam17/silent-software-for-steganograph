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
            
            # Use NumPy for efficient binary conversion
            text_bytes = text.encode('utf-8')
            text_bits = np.unpackbits(np.frombuffer(text_bytes, dtype=np.uint8))
            # Convert the binary string properly to bit values
            del_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            binary_array = np.concatenate([text_bits, del_bits])
            
            # Flatten the array for easier manipulation
            flat_array = img_array.flatten()

            # Check capacity
            if len(binary_array) > len(flat_array):
                return False, f"Text too large! Max {len(flat_array) // 8} bytes."

            # Efficiently apply bits to LSBs
            flat_array[:len(binary_array)] = (flat_array[:len(binary_array)] & 0xFE) | binary_array
            
            stego_array = flat_array.reshape(img_array.shape)
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
            
            # Extract LSBs efficiently using NumPy
            lsbs = (flat_array & 1).astype(np.uint8)
            
            # Convert delimiter to a numpy array of bits for efficient search
            # Convert the binary string properly to bit values
            delimiter_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            
            # Find the delimiter using optimized bit-shifted searches
            # We try all 8 bit-shifts to find the delimiter even if not byte-aligned
            found_index = -1
            del_packed = np.packbits(delimiter_bits).tobytes()
            
            for shift in range(8):
                shifted_lsbs = lsbs[shift:]
                # Pack the shifted bits into bytes
                lsbs_packed = np.packbits(shifted_lsbs).tobytes()
                found_byte_index = lsbs_packed.find(del_packed)
                
                if found_byte_index != -1:
                    found_index = (found_byte_index * 8) + shift
                    break
            
            if found_index == -1:
                return False, "No hidden message found or message is corrupted."
            
            # Extract the binary data before the delimiter
            binary_data_array = lsbs[:found_index]
            
            # Convert binary array to string for binary_to_text
            binary_data = "".join(map(str, binary_data_array))

            if callback:
                callback(75)
            
            # Convert binary to text
            extracted_text = binary_to_text(binary_data)
            
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
            
            header_bits = np.unpackbits(np.frombuffer(header.encode('utf-8'), dtype=np.uint8))
            data_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
            # Convert the binary string properly to bit values
            del_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            binary_array = np.concatenate([header_bits, data_bits, del_bits])
            
            # Open cover
            img = Image.open(cover_path)
            img_array = np.array(img)
            total_pixels = img_array.size
            if len(binary_array) > total_pixels:
                 return False, f"File too large! Max {total_pixels // 8} bytes."

            # Flatten and hide using vectorized ops
            flat_array = img_array.flatten()
            flat_array[:len(binary_array)] = (flat_array[:len(binary_array)] & 0xFE) | binary_array
            
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
            
            # Use NumPy to extract all LSBs
            lsbs = (flat_array & 1).astype(np.uint8)
            
            # Convert delimiter to a numpy array of bits for efficient search
            # Convert the binary string properly to bit values
            delimiter_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            
            # Find the delimiter using optimized bit-shifted searches
            delimiter_index = -1
            del_packed = np.packbits(delimiter_bits).tobytes()
            
            for shift in range(8):
                shifted_lsbs = lsbs[shift:]
                lsbs_packed = np.packbits(shifted_lsbs).tobytes()
                found_byte_index = lsbs_packed.find(del_packed)
                
                if found_byte_index != -1:
                    delimiter_index = (found_byte_index * 8) + shift
                    break
            
            if delimiter_index == -1:
                return False, "No steganographic header or delimiter found."

            # Extract header bits (up to the delimiter)
            header_and_data_bits = lsbs[:delimiter_index]
            
            # Convert bits to bytes and then to text to find the header
            # We need to find the '}}' within the extracted bits to separate header from data
            header_end_marker_binary = text_to_binary('}}')
            
            # Convert the relevant part of the binary array to a string for searching
            # This conversion is localized to the header part, not the entire image
            temp_binary_str = "".join(map(str, header_and_data_bits))
            
            header_end_in_temp_str = temp_binary_str.find(header_end_marker_binary)
            
            if header_end_in_temp_str == -1:
                return False, "No steganographic header found."
            
            header_binary_str = temp_binary_str[:header_end_in_temp_str + len(header_end_marker_binary)]
            header_text = binary_to_text(header_binary_str)
            
            import re
            match = re.search(r"{{FILE:(.+?),SIZE:(\d+)}}", header_text)
            if not match:
                return False, "Invalid file header format."
            
            filename = match.group(1)
            filesize = int(match.group(2))
            
            # The actual data bits start after the header_binary_str
            data_start_bit_index = len(header_binary_str)
            
            # Extract the data bits
            data_bits_array = header_and_data_bits[data_start_bit_index:]
            
            # Check if the extracted data bits match the expected filesize
            if len(data_bits_array) != filesize * 8:
                # This can happen if the image was too small or corrupted
                # Or if encryption added padding and the 'SIZE' refers to original size
                # For now, we'll proceed with what we extracted, but this is a potential point of failure
                pass 

            file_content = binary_to_bytes("".join(map(str, data_bits_array)))
            
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
