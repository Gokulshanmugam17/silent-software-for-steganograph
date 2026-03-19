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
            if not output_path.lower().endswith('.avi'):
                output_path = os.path.splitext(output_path)[0] + '.avi'
            
            # Try multiple codecs in order of preference
            codecs_to_try = ['XVID', 'H264', 'avc1', 'XMPG', 'MJPG']
            out = None
            
            for codec in codecs_to_try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                if out.isOpened():
                    break
            
            if not out or not out.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            text_bytes = text.encode('utf-8')
            text_bits = np.unpackbits(np.frombuffer(text_bytes, dtype=np.uint8))
            # Convert the binary string properly to bit values
            del_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            binary_array = np.concatenate([text_bits, del_bits])
            
            total_binary = len(binary_array)
            binary_index = 0
            frame_num = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if callback:
                    callback(int((frame_num / frame_count) * 100))
                
                if binary_index < total_binary:
                    flat = frame.ravel()
                    remaining = total_binary - binary_index
                    to_hide = min(remaining, len(flat))
                    flat[:to_hide] = (flat[:to_hide] & 0xFE) | binary_array[binary_index : binary_index + to_hide]
                    binary_index += to_hide
                
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
            all_frames_lsbs = []
            found = False
            frame_num = 0
            del_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            # Convert delimiter bits to bytes (pack 8 bits into 1 byte)
            del_bytes = np.packbits(del_bits).tobytes()
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if callback:
                    callback(int((frame_num / frame_count) * 45))
                
                lsbs = (frame.ravel() & 1).astype(np.uint8)
                all_frames_lsbs.append(lsbs)
                
                # Check for delimiter every 10 frames using faster byte search
                if len(all_frames_lsbs) % 10 == 0:
                    recent = np.concatenate(all_frames_lsbs[-12:])
                    recent_packed = np.packbits(recent).tobytes()
                    if del_bytes in recent_packed:
                        found = True
                        break
                frame_num += 1
            cap.release()
            
            if not all_frames_lsbs:
                return False, "No frames processed."
            
            full_lsbs = np.concatenate(all_frames_lsbs)
            
            # Use faster byte-based search
            full_packed = np.packbits(full_lsbs).tobytes()
            del_idx = full_packed.find(del_bytes)
            
            if del_idx == -1:
                return False, "No hidden message found."
            
            # Convert byte position back to bit position
            del_idx = del_idx * 8
            binary_data = "".join(map(str, full_lsbs[:del_idx]))
            
            if callback:
                callback(75)
            text = binary_to_text(binary_data)
            
            if password:
                try:
                    text = decrypt_message(text, password)
                except Exception as e:
                    from .utils import generate_decoy_message, wipe_file_data
                    if wipe_on_fail:
                        wipe_file_data(video_path)
                        return False, "Security Triggered: Data has been wiped."
                    if decoy_on_fail:
                        return True, generate_decoy_message()
                    return False, f"Decryption failed: Incorrect Password"

            from .utils import check_expiration, wipe_file_data
            is_expired, clean_text, has_header = check_expiration(text)
            if is_expired:
                wipe_file_data(video_path)
                return False, "⚠️ Dead-Man Switch Triggered: Message expired."
            if has_header:
                text = clean_text

            if callback:
                callback(100)
            return True, text
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def hide_video(self, cover_path: str, secret_path: str, output_path: str,
                   callback=None) -> Tuple[bool, str]:
        try:
            cover_cap = cv2.VideoCapture(cover_path)
            secret_cap = cv2.VideoCapture(secret_path)
            if not cover_cap.isOpened() or not secret_cap.isOpened():
                return False, "Could not open video files"
            
            width = int(cover_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cover_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cover_cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cover_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Get secret video properties
            secret_width = int(secret_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            secret_height = int(secret_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            secret_fps = secret_cap.get(cv2.CAP_PROP_FPS)
            secret_frame_count = int(secret_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if not output_path.lower().endswith('.avi'):
                output_path = os.path.splitext(output_path)[0] + '.avi'
            
            # Try multiple codecs in order of preference (compression efficiency)
            codecs_to_try = ['XVID', 'H264', 'avc1', 'XMPG', 'MJPG']
            out = None
            
            for codec in codecs_to_try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                if out.isOpened():
                    break
            
            if not out or not out.isOpened():
                # Last resort: try with default backend
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height), True)
            
            # Store metadata in the first frame using LSB
            # Metadata format: {{VIDEO_META:SW=width,SH=height,SF=fps,SN=frame_count}}
            metadata = f"{{{{VIDEO_META:SW={secret_width},SH={secret_height},SF={secret_fps},SN={secret_frame_count}}}}}"
            metadata_bytes = metadata.encode('utf-8')
            metadata_bits = np.unpackbits(np.frombuffer(metadata_bytes, dtype=np.uint8))
            
            frame_num = 0
            # Track secret frames separately
            ret_secret, secret_frame = secret_cap.read()
            
            while True:
                ret_cover, cover_frame = cover_cap.read()
                if not ret_cover: break
                if callback: callback(int((frame_num / frame_count) * 100))
                
                # Ensure frames are uint8 for proper bitwise operations
                if cover_frame is None:
                    break
                cover_frame = np.clip(cover_frame, 0, 255).astype(np.uint8)
                
                # Embed metadata in first frame (using 1-bit LSB)
                if frame_num == 0:
                    stego_frame = cover_frame.copy()
                    flat = stego_frame.ravel()
                    total_meta_bits = len(metadata_bits)
                    to_hide = min(total_meta_bits, len(flat))
                    flat[:to_hide] = (flat[:to_hide] & 0xFE) | metadata_bits[:to_hide]
                elif ret_secret and secret_frame is not None:
                    secret_frame = cv2.resize(secret_frame, (width, height))
                    secret_frame = np.clip(secret_frame, 0, 255).astype(np.uint8)
                    # 4-bit LSB steganography: hide upper 4 bits of secret in lower 4 bits of cover
                    stego_frame = np.zeros_like(cover_frame)
                    stego_frame[:, :, 0] = (cover_frame[:, :, 0] & 0xF0) | ((secret_frame[:, :, 0] >> 4) & 0x0F)  # Blue
                    stego_frame[:, :, 1] = (cover_frame[:, :, 1] & 0xF0) | ((secret_frame[:, :, 1] >> 4) & 0x0F)  # Green
                    stego_frame[:, :, 2] = (cover_frame[:, :, 2] & 0xF0) | ((secret_frame[:, :, 2] >> 4) & 0x0F)  # Red
                    # Read next secret frame for next iteration
                    ret_secret, secret_frame = secret_cap.read()
                else:
                    stego_frame = cover_frame
                
                out.write(stego_frame)
                frame_num += 1
            
            cover_cap.release()
            secret_cap.release()
            out.release()
            if callback: callback(100)
            return True, f"Video hidden successfully in {output_path}"
        except Exception as e:
            return False, f"Error hiding video: {str(e)}"
    
    def extract_video(self, stego_path: str, output_path: str,
                      callback=None) -> Tuple[bool, str]:
        try:
            import re
            cap = cv2.VideoCapture(stego_path)
            if not cap.isOpened():
                return False, "Could not open stego video file"
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            stego_fps = cap.get(cv2.CAP_PROP_FPS)
            stego_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Extract metadata from first frame
            ret, first_frame = cap.read()
            if not ret:
                cap.release()
                return False, "Could not read first frame"
            
            first_frame = np.clip(first_frame, 0, 255).astype(np.uint8)
            lsbs = (first_frame.ravel() & 1).astype(np.uint8)
            
            # Find metadata in LSBs
            del_arr = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            del_bytes = del_arr.tobytes()
            
            # Look for metadata pattern
            lsb_bytes = lsbs.tobytes()
            meta_match = re.search(rb'\{\{VIDEO_META:SW=(\d+),SH=(\d+),SF=([\d.]+),SN=(\d+)\}\}', lsb_bytes)
            
            if meta_match:
                secret_width = int(meta_match.group(1))
                secret_height = int(meta_match.group(2))
                secret_fps = float(meta_match.group(3))
                secret_frame_count = int(meta_match.group(4))
            else:
                # Fallback: assume metadata not found, use stego video properties
                secret_width = width
                secret_height = height
                secret_fps = stego_fps
                secret_frame_count = stego_frame_count - 1  # Assume first frame is metadata
            
            if not output_path.lower().endswith('.avi'):
                output_path = os.path.splitext(output_path)[0] + '.avi'
            
            # Use H264 for better compression (smaller file size)
            fourcc = cv2.VideoWriter_fourcc(*'H264')
            out = cv2.VideoWriter(output_path, fourcc, secret_fps, (secret_width, secret_height))
            
            if not out.isOpened():
                # Fallback to other codecs
                codecs_to_try = ['XVID', 'MJPG', 'avc1', 'XMPG']
                out = None
                for codec in codecs_to_try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    out = cv2.VideoWriter(output_path, fourcc, secret_fps, (secret_width, secret_height))
                    if out.isOpened():
                        break
            
            if not out or not out.isOpened():
                cap.release()
                return False, "Could not create output video writer"
            
            # Read and extract video frames (skip first frame which is metadata)
            frame_num = 0
            extracted_count = 0
            
            while extracted_count < secret_frame_count:
                ret, frame = cap.read()
                if not ret:
                    break
                if callback: callback(int((extracted_count / secret_frame_count) * 100))
                
                frame = np.clip(frame, 0, 255).astype(np.uint8)
                
                # Skip the first frame (metadata frame)
                if frame_num == 0:
                    frame_num += 1
                    continue
                
                # Extract the hidden video: get lower 4 bits and shift to upper 4 bits
                # Also resize to original secret video dimensions if different
                extracted_frame = np.zeros((secret_height, secret_width, 3), dtype=np.uint8)
                
                # Resize stego frame if needed
                if width != secret_width or height != secret_height:
                    frame = cv2.resize(frame, (secret_width, secret_height))
                
                extracted_frame[:, :, 0] = ((frame[:, :, 0] & 0x0F) << 4)  # Blue
                extracted_frame[:, :, 1] = ((frame[:, :, 1] & 0x0F) << 4)  # Green
                extracted_frame[:, :, 2] = ((frame[:, :, 2] & 0x0F) << 4)  # Red
                
                out.write(extracted_frame)
                extracted_count += 1
                frame_num += 1
            
            cap.release()
            out.release()
            
            if extracted_count < secret_frame_count:
                return True, f"Video extracted ({extracted_count} frames) to {output_path}"
            
            if callback: callback(100)
            return True, f"Video extracted successfully to {output_path}"
        except Exception as e:
            return False, f"Error extracting video: {str(e)}"

    def hide_file(self, cover_path: str, file_path: str, output_path: str, 
                  password: Optional[str] = None, callback=None) -> Tuple[bool, str]:
        try:
            from .utils import encrypt_data
            with open(file_path, "rb") as f:
                data = f.read()
            
            filename = os.path.basename(file_path)
            if password:
                data = encrypt_data(data, password)
            
            header = f"{{{{FILE:{filename},SIZE:{len(data)}}}}}"
            header_bits = np.unpackbits(np.frombuffer(header.encode('utf-8'), dtype=np.uint8))
            data_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
            # Convert the binary string properly to bit values
            del_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            
            binary_array = np.concatenate([header_bits, data_bits, del_bits])
            total_binary = len(binary_array)
            binary_index = 0
            frame_num = 0
            
            cap = cv2.VideoCapture(cover_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if not output_path.lower().endswith('.avi'):
                output_path = os.path.splitext(output_path)[0] + '.avi'
                
            # Try multiple codecs in order of preference
            codecs_to_try = ['XVID', 'H264', 'avc1', 'XMPG', 'MJPG']
            out = None
            
            for codec in codecs_to_try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                if out.isOpened():
                    break
            
            if not out or not out.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            while True:
                ret, frame = cap.read()
                if not ret: break
                if callback: callback(int((frame_num / frame_count) * 100))
                    
                if binary_index < total_binary:
                    flat = frame.ravel()
                    remaining = total_binary - binary_index
                    to_hide = min(remaining, len(flat))
                    flat[:to_hide] = (flat[:to_hide] & 0xFE) | binary_array[binary_index : binary_index + to_hide]
                    binary_index += to_hide
                    
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
        try:
            from .utils import binary_to_bytes, decrypt_data
            cap = cv2.VideoCapture(stego_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            all_frames_lsbs = []
            found = False
            frame_num = 0
            del_bits = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            # Convert delimiter bits to bytes (pack 8 bits into 1 byte)
            del_bytes = np.packbits(del_bits).tobytes()
            
            while True:
                ret, frame = cap.read()
                if not ret: break
                if callback: callback(int((frame_num / frame_count) * 40))
                lsbs = (frame.ravel() & 1).astype(np.uint8)
                all_frames_lsbs.append(lsbs)
                
                # Check for delimiter every 10 frames using faster byte search
                if len(all_frames_lsbs) % 10 == 0:
                    recent = np.concatenate(all_frames_lsbs[-12:])
                    recent_packed = np.packbits(recent).tobytes()
                    if del_bytes in recent_packed:
                        found = True
                        break
                frame_num += 1
                
            cap.release()
            
            if not all_frames_lsbs:
                return False, "No frames processed."
            
            full_lsbs = np.concatenate(all_frames_lsbs)
            
            # Use faster byte-based search
            full_packed = np.packbits(full_lsbs).tobytes()
            del_idx = full_packed.find(del_bytes)
            
            if del_idx == -1:
                return False, "No hidden file found."
            
            # Convert byte position back to bit position
            del_idx = del_idx * 8

            binary_data_arr = full_lsbs[:del_idx]
            full_bytes = binary_to_bytes("".join(map(str, binary_data_arr)))
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
