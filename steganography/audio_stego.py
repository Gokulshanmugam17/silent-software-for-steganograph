import wave
import numpy as np
import os
from typing import Optional, Tuple
from pydub import AudioSegment
from .utils import text_to_binary, binary_to_text, get_delimiter, encrypt_message, decrypt_message


class AudioSteganography:
    """Class for hiding and extracting data from audio files."""
    
    def __init__(self):
        self.delimiter = get_delimiter()
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.mpeg', '.aac', '.wma', '.aiff']
    
    def get_audio_info(self, audio_path: str) -> dict:
        """Get information about an audio file."""
        try:
            # Handle various formats using pydub
            audio = AudioSegment.from_file(audio_path)
            
            frames = int(audio.frame_count())
            sample_width = audio.sample_width
            channels = audio.channels
            framerate = audio.frame_rate
            duration = audio.duration_seconds
            
            # Calculate capacity (1 bit per sample)
            capacity = frames * channels // 8
            
            return {
                'frames': frames,
                'sample_width': sample_width,
                'channels': channels,
                'framerate': framerate,
                'duration': round(float(duration), 2),
                'capacity': capacity
            }
        except Exception as e:
            # Fallback to wave for basic wav files if pydub fails
            try:
                with wave.open(audio_path, 'rb') as audio:
                    frames = audio.getnframes()
                    sample_width = audio.getsampwidth()
                    channels = audio.getnchannels()
                    framerate = audio.getframerate()
                    duration = frames / framerate
                    capacity = frames * channels // 8
                    
                    return {
                        'frames': frames,
                        'sample_width': sample_width,
                        'channels': channels,
                        'framerate': framerate,
                        'duration': round(float(duration), 2),
                        'capacity': capacity
                    }
            except:
                raise ValueError(f"Could not read audio: {str(e)}")

    def _read_audio_data(self, audio_path: str) -> Tuple[np.ndarray, dict, AudioSegment]:
        """Read audio data and return numpy array and parameters normalized to 16-bit PCM."""
        try:
            audio = AudioSegment.from_file(audio_path)
        except Exception as e:
            if "ffmpeg" in str(e).lower() or "avconv" in str(e).lower():
                raise RuntimeError("FFmpeg is not installed or not in PATH. Please install FFmpeg to support non-WAV formats (MP3, MPEG, etc.)")
            raise ValueError(f"Could not read audio file: {str(e)}")
        
        # Normalize to 16-bit PCM for consistent steganography
        # This is the "change into wav format" part - ensuring we work with 16-bit samples
        if audio.sample_width != 2:
            audio = audio.set_sample_width(2)
        
        # Get parameters
        params = {
            'nchannels': audio.channels,
            'sampwidth': audio.sample_width,
            'framerate': audio.frame_rate,
            'nframes': int(audio.frame_count()),
            'comptype': 'NONE',
            'compname': 'not compressed'
        }
        
        # Consistent dtype after normalization
        dtype = np.int16
        samples = np.array(audio.get_array_of_samples(), dtype=dtype)
        
        return samples, params, audio
    
    def hide_text(self, audio_path: str, text: str, output_path: str,
                  password: Optional[str] = None, callback=None, expiry_hours: float = 0) -> Tuple[bool, str]:
        """
        Hide text in an audio file using LSB steganography.
        
        Args:
            audio_path: Path to the source audio file
            text: Text to hide
            output_path: Path to save the output audio
            password: Optional password for encryption
            callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Open the audio file and get samples
            audio_array, params, audio_segment = self._read_audio_data(audio_path)
            audio_array = audio_array.copy()
            
            # Since we normalized to 16-bit PCM in _read_audio_data, dtype is always int16
            dtype = np.int16
            
            # Prepare the message
            if expiry_hours > 0:
                from .utils import add_expiration
                text = add_expiration(text, expiry_hours)
                
            if password:
                text = encrypt_message(text, password)
            
            # Use NumPy for efficient binary conversion
            text_bytes = text.encode('utf-8')
            text_bits = np.unpackbits(np.frombuffer(text_bytes, dtype=np.uint8))
            # Convert the binary string properly to bit values
            del_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            binary_array = np.concatenate([text_bits, del_bits])
            
            if len(binary_array) > len(audio_array):
                return False, f"Text too large! Maximum {len(audio_array) // 8} bytes allowed."
            
            # Efficiently apply bits to LSBs using NumPy
            audio_array[:len(binary_array)] = (audio_array[:len(binary_array)] & ~1) | binary_array
            
            # Ensure output is WAV for stego integrity
            if not output_path.lower().endswith('.wav'):
                output_path += '.wav'
            
            # Save the modified audio using pydub
            new_audio = audio_segment._spawn(audio_array.tobytes())
            new_audio.export(output_path, format="wav")
            
            if callback:
                callback(100)
            
            return True, f"Text hidden successfully in {output_path}"
            
        except Exception as e:
            return False, f"Error hiding text: {str(e)}"
    
    def extract_text(self, audio_path: str, password: Optional[str] = None,
                     callback=None, decoy_on_fail: bool = False, wipe_on_fail: bool = False) -> Tuple[bool, str]:
        """
        Extract hidden text from an audio file.
        
        Args:
            audio_path: Path to the stego audio file
            password: Optional password for decryption
            callback: Optional callback function for progress updates
            decoy_on_fail: Return fake data if password fails
            wipe_on_fail: Corrupt data if password fails
            
        Returns:
            Tuple of (success, message/extracted_text)
        """
        try:
            # Open the audio file and get samples
            audio_array, params, _ = self._read_audio_data(audio_path)
            
            # Extract LSBs efficiently using NumPy
            lsbs = (audio_array & 1).astype(np.uint8)
            
            # Convert delimiter to bits for search
            # Convert the binary string properly to bit values
            delimiter_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            
            # Find delimiter
            found_index = -1
            # Check in chunks to improve speed
            for i in range(0, len(lsbs) - len(delimiter_bits), 8):
                if np.array_equal(lsbs[i : i + len(delimiter_bits)], delimiter_bits):
                    found_index = i
                    break
            
            if found_index == -1:
                return False, "No hidden message found or message is corrupted."
            
            binary_data = "".join(map(str, lsbs[:found_index]))
            found = True
            
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
                        wipe_file_data(audio_path)
                        return False, "Security Triggered: Data has been wiped."
                    
                    if decoy_on_fail:
                        return True, generate_decoy_message()

                    return False, f"Decryption failed: {str(e)}"
            
            # Check for Expiration
            from .utils import check_expiration, wipe_file_data
            is_expired, clean_text, has_header = check_expiration(extracted_text)
            
            if is_expired:
                wipe_file_data(audio_path)
                return False, "⚠️ Dead-Man Switch Triggered: Message expired and self-destructed."
                
            if has_header:
                extracted_text = clean_text
            
            if callback:
                callback(100)
            
            return True, extracted_text
            
        except Exception as e:
            return False, f"Error extracting text: {str(e)}"
    
    def hide_audio(self, cover_path: str, secret_path: str, output_path: str,
                   password: Optional[str] = None, callback=None) -> Tuple[bool, str]:
        """
        Hide an audio file inside another audio file.
        Uses 4-bit MSB substitution with normalization and optional encryption.
        
        Args:
            cover_path: Path to the cover audio
            secret_path: Path to the secret audio
            output_path: Path to save the output
            password: Optional password for encryption
            callback: Optional callback function
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Read cover audio
            cover_array, cover_params, cover_segment = self._read_audio_data(cover_path)
            cover_array = cover_array.copy()
            
            # Read and normalize secret audio to match cover
            secret_segment = AudioSegment.from_file(secret_path)
            
            # Match framerate and channels
            if secret_segment.frame_rate != cover_segment.frame_rate:
                secret_segment = secret_segment.set_frame_rate(cover_segment.frame_rate)
            if secret_segment.channels != cover_segment.channels:
                secret_segment = secret_segment.set_channels(cover_segment.channels)
            if secret_segment.sample_width != 2:
                secret_segment = secret_segment.set_sample_width(2)
                
            # Get secret array from normalized segment
            secret_array = np.array(secret_segment.get_array_of_samples(), dtype=np.int16)
            
            # Pad or truncate secret to match cover length
            if len(secret_array) < len(cover_array):
                # Add tiny random noise to the padding to avoid absolute silence patterns
                padding_len = len(cover_array) - len(secret_array)
                padding = np.random.randint(-5, 5, padding_len, dtype=np.int16)
                secret_array = np.concatenate([secret_array, padding])
            else:
                secret_array = secret_array[:len(cover_array)]
            
            # Encrypt secret bits if password provided
            if password:
                from .utils import generate_key
                # Generate a simple stream key from password
                key = generate_key(password)
                # Expand key to match array length (using seed for reproducibility)
                import hashlib
                seed = int(hashlib.md5(key).hexdigest(), 16) % (2**32)
                np.random.seed(seed)
                # Create XOR mask for the 4 bits we'll hide (0x0...0x000F)
                xor_mask = np.random.randint(0, 16, len(secret_array), dtype=np.int16)
            else:
                xor_mask = np.zeros(len(secret_array), dtype=np.int16)
            
            # Combine: Hide 4 MSBs of secret in 4 LSBs of cover
            # (secret_array >> 12) extracts top 4 bits. 
            # XORed with mask for security.
            secret_bits = ((secret_array >> 12) & 0x000F) ^ (xor_mask & 0x000F)
            
            # Use uint16 for bitwise manipulation to avoid signed overflow/out-of-bounds errors in NumPy
            u_cover = cover_array.astype(np.uint16)
            u_stego = (u_cover & 0xFFF0) | (secret_bits.astype(np.uint16) & 0x000F)
            stego_array = u_stego.astype(np.int16)
            
            # Ensure output is WAV for stego integrity
            if not output_path.lower().endswith('.wav'):
                output_path += '.wav'
            
            # Save using pydub
            new_audio = cover_segment._spawn(stego_array.tobytes())
            new_audio.export(output_path, format="wav")
            
            if callback:
                callback(100)
            
            return True, f"Audio hidden successfully in {output_path}"
            
        except Exception as e:
            return False, f"Error hiding audio: {str(e)}"
    
    def extract_audio(self, stego_path: str, output_path: str,
                      password: Optional[str] = None, callback=None) -> Tuple[bool, str]:
        """
        Extract hidden audio from a stego audio file.
        
        Args:
            stego_path: Path to the stego audio
            output_path: Path to save the extracted audio
            password: Optional password for decryption
            callback: Optional callback function
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Read stego audio
            stego_array, params, stego_segment = self._read_audio_data(stego_path)
            
            # Extract 4 LSBs using uint16 to avoid signed bitwise unexpected behaviors
            u_stego = stego_array.astype(np.uint16)
            extracted_bits = (u_stego & 0x000F).astype(np.int16)
            
            # Decrypt if password provided
            if password:
                from .utils import generate_key
                key = generate_key(password)
                import hashlib
                seed = int(hashlib.md5(key).hexdigest(), 16) % (2**32)
                np.random.seed(seed)
                xor_mask = np.random.randint(0, 16, len(stego_array), dtype=np.int16)
                extracted_bits = extracted_bits ^ (xor_mask & 0x000F)
            
            # Shift back to MSB position
            extracted_array = (extracted_bits << 12).astype(np.int16)
            
            # Ensure output is WAV
            if not output_path.lower().endswith('.wav'):
                output_path += '.wav'
            
            # Save extracted audio
            new_audio = stego_segment._spawn(extracted_array.tobytes())
            new_audio.export(output_path, format="wav")
            
            if callback:
                callback(100)
            
            return True, f"Audio extracted successfully to {output_path}"
            
        except Exception as e:
            return False, f"Error extracting audio: {str(e)}"

    def hide_file(self, cover_path: str, file_path: str, output_path: str, 
                  password: Optional[str] = None, callback=None) -> Tuple[bool, str]:
        """Hide any file inside an audio file."""
        try:
            from .utils import bytes_to_binary, encrypt_data
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
            
            # Read cover audio
            audio_array, params, audio_segment = self._read_audio_data(cover_path)
            audio_array = audio_array.copy()
            
            if len(binary_array) > len(audio_array):
                return False, f"File too large! Content needs {len(binary_array)} bits, but only {len(audio_array)} bits available."

            # Efficiently apply bits to LSBs using NumPy
            audio_array[:len(binary_array)] = (audio_array[:len(binary_array)] & ~1) | binary_array

            # Ensure output is WAV
            if not output_path.lower().endswith('.wav'):
                output_path += '.wav'
            
            # Save using pydub
            new_audio = audio_segment._spawn(audio_array.tobytes())
            new_audio.export(output_path, format="wav")
            
            if callback: callback(100)
            return True, f"File hidden in {output_path}"
        except Exception as e:
            return False, f"Error: {e}"

    def extract_file(self, stego_path: str, output_folder: str, 
                     password: Optional[str] = None, callback=None) -> Tuple[bool, str]:
        """Extract hidden file from stego audio."""
        try:
            from .utils import binary_to_bytes, decrypt_data
            
            # Read stego audio
            audio_array, params, _ = self._read_audio_data(stego_path)
            
            # Use NumPy to extract all LSBs
            lsbs = (audio_array & 1).astype(np.uint8)
            
            # Find delimiter
            # Convert the binary string properly to bit values
            delimiter_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            delimiter_index = -1
            for i in range(0, len(lsbs) - len(delimiter_bits), 8):
                if np.array_equal(lsbs[i : i + len(delimiter_bits)], delimiter_bits):
                    delimiter_index = i
                    break

            if delimiter_index == -1:
                return False, "No hidden file found."

            # Efficiently extract header and data
            header_end_marker_bits = (np.fromiter(text_to_binary('}}'), dtype='u1') - 48).astype(np.uint8)
            header_end_index = -1
            for i in range(0, delimiter_index - len(header_end_marker_bits), 8):
                if np.array_equal(lsbs[i : i + len(header_end_marker_bits)], header_end_marker_bits):
                    header_end_index = i
                    break
            
            if header_end_index == -1:
                return False, "Invalid file format (No header detected)."
            
            header_binary = "".join(map(str, lsbs[:header_end_index + 16])) # 16 bits for '}}'
            header_text = binary_to_text(header_binary)
            
            import re
            match = re.search(r"{{FILE:(.+?),SIZE:(\d+)}}", header_text)
            if not match: return False, "Invalid header format."
            
            filename = match.group(1)
            filesize = int(match.group(2))
            
            data_start = header_end_index + 16
            binary_data = "".join(map(str, lsbs[data_start : data_start + filesize * 8]))
            found = True
            
            if not found: return False, "No hidden file found."
            
            if callback: callback(75)
            full_bytes = binary_to_bytes(binary_data)
            header_end = full_bytes.find(b'}}')
            if header_end == -1: return False, "Invalid file format (No header detected)."
            
            header_part = full_bytes[:header_end+2]
            file_content = full_bytes[header_end+2:]
            
            import re
            header_str = header_part.decode('utf-8', errors='ignore')
            match = re.search(r"{{FILE:(.+?),SIZE:(\d+)}}", header_str)
            if not match: return False, "Invalid header format."
            
            filename = match.group(1)
            filesize = int(match.group(2))
            file_content = file_content[:filesize]
            
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

    def convert_to_wav(self, audio_path: str, output_path: str) -> bool:
        """
        Explicitly convert any audio format to a standard WAV file.
        This fulfills the requirement of 'upload any format change into wav'.
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            # Standardize to 16-bit PCM, 44.1kHz, Stereo
            audio = audio.set_sample_width(2).set_frame_rate(44100).set_channels(2)
            audio.export(output_path, format="wav")
            return True
        except Exception as e:
            print(f"Error converting to WAV: {e}")
            return False
