"""
Video Steganography Module
Supports hiding text and video data in video files using frame-based LSB technique.
"""
import cv2
import numpy as np
import os
from typing import Optional, Tuple
from .utils import text_to_binary, binary_to_text, get_delimiter, encrypt_message, decrypt_message


class VideoSteganography:
    def __init__(self):
        self.delimiter = get_delimiter()
        self.supported_formats = ['.avi', '.mp4', '.mkv']
    
    def get_video_info(self, video_path: str) -> dict:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        capacity = (width * height * 3 // 8) * frame_count
        cap.release()
        return {'width': width, 'height': height, 'fps': fps, 'frame_count': frame_count,
                'duration': round(float(duration), 2), 'total_capacity': capacity}
    
    def hide_text(self, video_path: str, text: str, output_path: str,
                  password: Optional[str] = None, callback=None, expiry_hours: float = 0) -> Tuple[bool, str]:
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, "Could not open video file"
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if expiry_hours > 0:
                from .utils import add_expiration
                text = add_expiration(text, expiry_hours)

            if password:
                text = encrypt_message(text, password)
            binary_text = text_to_binary(text) + self.delimiter
            if not output_path.lower().endswith('.avi'):
                output_path = os.path.splitext(output_path)[0] + '.avi'
            
            # Use FFV1 for lossless video encoding to protect steganographic data
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                # Fallback to a safer but perhaps lossy codec if FFV1 is missing, 
                # though FFV1 is standard in most FFmpeg builds.
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            binary_index = 0
            total_binary = len(binary_text)
            frame_num = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if callback:
                    callback(int((frame_num / frame_count) * 100))
                if binary_index < total_binary:
                    flat = frame.flatten()
                    for i in range(len(flat)):
                        if binary_index >= total_binary:
                            break
                        flat[i] = (flat[i] & 0xFE) | int(binary_text[binary_index])
                        binary_index += 1
                    frame = flat.reshape(frame.shape)
                out.write(frame)
                frame_num += 1
            cap.release()
            out.release()
            if callback:
                callback(100)
            return True, f"Text hidden successfully in {output_path}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def extract_text(self, video_path: str, password: Optional[str] = None,
                     callback=None, decoy_on_fail: bool = False, wipe_on_fail: bool = False) -> Tuple[bool, str]:
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, "Could not open video file"
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            binary_bits = []
            found = False
            frame_num = 0
            del_len = len(self.delimiter)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if callback:
                    callback(int((frame_num / frame_count) * 50))
                
                flat_frame = frame.flatten()
                for pixel in flat_frame:
                    binary_bits.append(str(pixel & 1))
                    
                    # Check for delimiter only at byte boundaries for efficiency
                    if len(binary_bits) >= del_len and len(binary_bits) % 8 == 0:
                        if "".join(binary_bits[-del_len:]) == self.delimiter:
                            binary_data = "".join(binary_bits[:-del_len])
                            found = True
                            break
                if found:
                    break
                frame_num += 1
            cap.release()
            if not found:
                return False, "No hidden message found."
            if callback:
                callback(75)
            text = binary_to_text(binary_data)
            
            if password:
                try:
                    text = decrypt_message(text, password)
                except Exception as e:
                    # Security Features Trigger
                    from .utils import generate_decoy_message, wipe_file_data
                    
                    if wipe_on_fail:
                        wipe_file_data(video_path)
                        return False, "Security Triggered: Data has been wiped."
                    
                    if decoy_on_fail:
                        return True, generate_decoy_message()
                        
                    return False, f"Decryption failed: Incorrect Password"

            # Check for Expiration
            from .utils import check_expiration, wipe_file_data
            is_expired, clean_text, has_header = check_expiration(text)
            
            if is_expired:
                wipe_file_data(video_path)
                return False, "⚠️ Dead-Man Switch Triggered: Message expired and self-destructed."
                
            if has_header:
                text = clean_text

            if callback:
                callback(100)
            return True, text
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def hide_video(self, cover_path: str, secret_path: str, output_path: str,
                   callback=None) -> Tuple[bool, str]:
        """
        Hide a video inside another video using frame-based steganography.
        """
        try:
            cover_cap = cv2.VideoCapture(cover_path)
            secret_cap = cv2.VideoCapture(secret_path)
            
            if not cover_cap.isOpened():
                return False, "Could not open cover video"
            if not secret_cap.isOpened():
                cover_cap.release()
                return False, "Could not open secret video"
            
            # Get cover properties
            width = int(cover_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cover_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cover_cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cover_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Ensure output is AVI
            if not output_path.lower().endswith('.avi'):
                output_path = os.path.splitext(output_path)[0] + '.avi'
            
            # Use FFV1 for lossless video encoding
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_num = 0
            
            while True:
                ret_cover, cover_frame = cover_cap.read()
                if not ret_cover:
                    break
                
                ret_secret, secret_frame = secret_cap.read()
                
                if callback:
                    callback(int((frame_num / frame_count) * 100))
                
                if ret_secret:
                    # Resize secret frame to match cover
                    secret_frame = cv2.resize(secret_frame, (width, height))
                    # Combine: 4 MSBs from cover, 4 MSBs from secret
                    stego_frame = (cover_frame & 0xF0) | (secret_frame >> 4)
                else:
                    stego_frame = cover_frame
                
                out.write(stego_frame)
                frame_num += 1
            
            cover_cap.release()
            secret_cap.release()
            out.release()
            
            if callback:
                callback(100)
            
            return True, f"Video hidden successfully in {output_path}"
            
        except Exception as e:
            return False, f"Error hiding video: {str(e)}"
    
    def extract_video(self, stego_path: str, output_path: str,
                      callback=None) -> Tuple[bool, str]:
        """
        Extract hidden video from a stego video.
        """
        try:
            cap = cv2.VideoCapture(stego_path)
            if not cap.isOpened():
                return False, "Could not open stego video"
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Use FFV1 for lossless video encoding
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_num = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if callback:
                    callback(int((frame_num / frame_count) * 100))
                
                # Extract 4 LSBs and shift to MSB
                extracted_frame = (frame & 0x0F) << 4
                out.write(extracted_frame)
                frame_num += 1
            
            cap.release()
            out.release()
            
            if callback:
                callback(100)
            
            return True, f"Video extracted successfully to {output_path}"
            
        except Exception as e:
            return False, f"Error extracting video: {str(e)}"

    def hide_file(self, cover_path: str, file_path: str, output_path: str, 
                  password: Optional[str] = None, callback=None) -> Tuple[bool, str]:
        """Hide any file inside a video file."""
        try:
            from .utils import bytes_to_binary, encrypt_data
            with open(file_path, "rb") as f:
                data = f.read()
            
            filename = os.path.basename(file_path)
            
            if password:
                data = encrypt_data(data, password)
            
            header = f"{{{{FILE:{filename},SIZE:{len(data)}}}}}"
            full_binary = text_to_binary(header) + bytes_to_binary(data) + self.delimiter
            
            cap = cv2.VideoCapture(cover_path)
            if not cap.isOpened():
                return False, "Could not open video file"
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if not output_path.lower().endswith('.avi'):
                output_path = os.path.splitext(output_path)[0] + '.avi'
                
            # Use FFV1 for lossless video encoding
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            binary_index = 0
            total_binary = len(full_binary)
            frame_num = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if callback:
                    callback(int((frame_num / frame_count) * 100))
                    
                if binary_index < total_binary:
                    flat = frame.flatten()
                    for i in range(len(flat)):
                        if binary_index >= total_binary:
                            break
                        flat[i] = (flat[i] & 0xFE) | int(full_binary[binary_index])
                        binary_index += 1
                    frame = flat.reshape(frame.shape)
                    
                out.write(frame)
                frame_num += 1
                
            cap.release()
            out.release()
            
            if binary_index < total_binary:
                 return False, f"Video too small! Missing {total_binary - binary_index} bits."

            if callback: callback(100)
            return True, f"File hidden in {output_path}"
        except Exception as e:
            return False, f"Error: {e}"

    def extract_file(self, stego_path: str, output_folder: str, 
                     password: Optional[str] = None, callback=None) -> Tuple[bool, str]:
        """Extract hidden file from stego video."""
        try:
            from .utils import binary_to_bytes, decrypt_data
            cap = cv2.VideoCapture(stego_path)
            if not cap.isOpened():
                return False, "Could not open video file"
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            binary_bits = []
            found = False
            frame_num = 0
            del_len = len(self.delimiter)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if callback:
                    callback(int((frame_num / frame_count) * 50))
                    
                flat_frame = frame.flatten()
                for pixel in flat_frame:
                    binary_bits.append(str(pixel & 1))
                    
                    if len(binary_bits) >= del_len and len(binary_bits) % 8 == 0:
                        if "".join(binary_bits[-del_len:]) == self.delimiter:
                            binary_data = "".join(binary_bits[:-del_len])
                            found = True
                            break
                
                if found:
                    break
                frame_num += 1
                
            cap.release()
            if not found: return False, "No hidden file found."
            
            if callback: callback(75)
            full_bytes = binary_to_bytes(binary_data)
            header_end = full_bytes.find(b'}}')
            if header_end == -1: return False, "Invalid file format."
            
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

