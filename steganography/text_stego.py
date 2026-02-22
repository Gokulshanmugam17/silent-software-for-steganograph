"""
Text Steganography Module

Hides secret text within cover text using zero-width characters.
"""

from typing import Optional, Tuple
from .utils import encrypt_message, decrypt_message


class TextSteganography:
    """Class for hiding text within text using zero-width characters."""
    
    def __init__(self):
        # Zero-width characters for binary encoding
        self.ZERO = '\u200B'  # Zero-width space (represents 0)
        self.ONE = '\u200C'   # Zero-width non-joiner (represents 1)
        self.DELIMITER = '\u200D' * 3  # Zero-width joiner as delimiter
    
    def _text_to_binary(self, text: str) -> str:
        """Convert text to binary string."""
        return ''.join(format(ord(char), '08b') for char in text)
    
    def _binary_to_text(self, binary: str) -> str:
        """Convert binary string to text."""
        chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
        return ''.join(chr(int(char, 2)) for char in chars if len(char) == 8)
    
    def _binary_to_zwc(self, binary: str) -> str:
        """Convert binary string to zero-width characters."""
        return ''.join(self.ONE if bit == '1' else self.ZERO for bit in binary)
    
    def _zwc_to_binary(self, zwc_text: str) -> str:
        """Extract binary from zero-width characters."""
        binary = ''
        for char in zwc_text:
            if char == self.ZERO:
                binary += '0'
            elif char == self.ONE:
                binary += '1'
        return binary
    
    def hide_text(self, cover_text: str, secret_text: str, 
                  password: Optional[str] = None, callback=None,
                  expiry_hours: float = 0) -> Tuple[bool, str]:
        """
        Hide secret text within cover text using zero-width characters.
        
        Args:
            cover_text: The visible cover text
            secret_text: The secret message to hide
            password: Optional password for encryption
            callback: Optional callback for progress
            expiry_hours: Optional expiration time in hours
            
        Returns:
            Tuple of (success, stego_text or error_message)
        """
        try:
            if not cover_text or not cover_text.strip():
                return False, "Cover text cannot be empty"
            
            if not secret_text or not secret_text.strip():
                return False, "Secret text cannot be empty"
            
            # Add expiration if requested
            if expiry_hours > 0:
                from .utils import add_expiration
                secret_text = add_expiration(secret_text, expiry_hours)
            
            # Encrypt if password provided
            if password:
                secret_text = encrypt_message(secret_text, password)
            
            if callback:
                callback(25)
            
            # Convert secret to binary then to zero-width characters
            binary = self._text_to_binary(secret_text)
            zwc = self._binary_to_zwc(binary) + self.DELIMITER
            
            if callback:
                callback(75)
            
            # Insert zero-width characters after the first sentence or midpoint
            insert_pos = cover_text.find('. ')
            if insert_pos == -1:
                insert_pos = len(cover_text) // 2
            else:
                insert_pos += 2  # After ". "
            
            stego_text = cover_text[:insert_pos] + zwc + cover_text[insert_pos:]
            
            if callback:
                callback(100)
            
            return True, stego_text
            
        except Exception as e:
            return False, f"Error hiding text: {str(e)}"
    
    def extract_text(self, stego_text: str, password: Optional[str] = None,
                     callback=None, decoy_on_fail: bool = False) -> Tuple[bool, str]:
        """
        Extract hidden text from stego text.
        
        Args:
            stego_text: Text containing hidden message
            password: Optional password for decryption
            callback: Optional callback for progress
            decoy_on_fail: Return decoy message on failure
            
        Returns:
            Tuple of (success, extracted_text or error_message)
        """
        try:
            if not stego_text:
                return False, "Stego text cannot be empty"
            
            if callback:
                callback(25)
            
            # Extract zero-width characters
            zwc_chars = ''
            for char in stego_text:
                if char in (self.ZERO, self.ONE, self.DELIMITER[0]):
                    zwc_chars += char
            
            if not zwc_chars:
                return False, "No hidden message found"
            
            # Find delimiter
            delimiter_pos = zwc_chars.find(self.DELIMITER)
            if delimiter_pos == -1:
                return False, "Invalid or corrupted hidden message"
            
            zwc_message = zwc_chars[:delimiter_pos]
            
            if callback:
                callback(50)
            
            # Convert back to binary then text
            binary = self._zwc_to_binary(zwc_message)
            extracted_text = self._binary_to_text(binary)
            
            if callback:
                callback(75)
            
            # Decrypt if password provided
            if password:
                try:
                    extracted_text = decrypt_message(extracted_text, password)
                except Exception as e:
                    if decoy_on_fail:
                        from .utils import generate_decoy_message
                        return True, generate_decoy_message()
                    return False, f"Decryption failed: Incorrect password"
            
            # Check for expiration
            from .utils import check_expiration
            is_expired, clean_text, has_header = check_expiration(extracted_text)
            
            if is_expired:
                return False, "⚠️ Dead-Man Switch Triggered: Message expired."
            
            if has_header:
                extracted_text = clean_text
            
            if callback:
                callback(100)
            
            return True, extracted_text
            
        except Exception as e:
            return False, f"Error extracting text: {str(e)}"
    
    def get_capacity(self, cover_text: str) -> int:
        """
        Calculate approximate capacity in characters.
        
        Args:
            cover_text: The cover text
            
        Returns:
            Maximum secret text length in characters
        """
        # Very rough estimate - zero-width chars don't affect visual length
        # but we want to be conservative
        return len(cover_text) * 2
