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
            
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            text_bytes = text.encode('utf-8')
            text_bits = np.unpackbits(np.frombuffer(text_bytes, dtype=np.uint8))
            del_bits = (np.fromiter(self.delimiter, dtype='u1') - 48).astype(np.uint8)
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
            del_arr = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            del_bytes = del_arr.tobytes()
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if callback:
                    callback(int((frame_num / frame_count) * 45))
                
                lsbs = (frame.ravel() & 1).astype(np.uint8)
                all_frames_lsbs.append(lsbs)
                
                if len(all_frames_lsbs) % 10 == 0:
                    recent = np.concatenate(all_frames_lsbs[-12:])
                    if recent.tobytes().find(del_bytes) != -1:
                        found = True
                        break
                frame_num += 1
            cap.release()
            
            if not found:
                if not all_frames_lsbs: return False, "No frames processed."
                full_lsbs = np.concatenate(all_frames_lsbs)
                del_idx = full_lsbs.tobytes().find(del_bytes)
                if del_idx == -1: return False, "No hidden message found."
            else:
                full_lsbs = np.concatenate(all_frames_lsbs)
                del_idx = full_lsbs.tobytes().find(del_bytes)
            
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
            
            if not output_path.lower().endswith('.avi'):
                output_path = os.path.splitext(output_path)[0] + '.avi'
            
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_num = 0
            while True:
                ret_cover, cover_frame = cover_cap.read()
                if not ret_cover: break
                ret_secret, secret_frame = secret_cap.read()
                if callback: callback(int((frame_num / frame_count) * 100))
                
                if ret_secret:
                    secret_frame = cv2.resize(secret_frame, (width, height))
                    stego_frame = (cover_frame & 0xF0) | (secret_frame >> 4)
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
            cap = cv2.VideoCapture(stego_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_num = 0
            while True:
                ret, frame = cap.read()
                if not ret: break
                if callback: callback(int((frame_num / frame_count) * 100))
                extracted_frame = (frame & 0x0F) << 4
                out.write(extracted_frame)
                frame_num += 1
            
            cap.release()
            out.release()
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
            del_bits = (np.fromiter(self.delimiter, dtype='u1') - 48).astype(np.uint8)
            
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
                
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
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
            del_arr = np.array([int(b) for b in self.delimiter], dtype=np.uint8)
            del_bytes = del_arr.tobytes()
            
            while True:
                ret, frame = cap.read()
                if not ret: break
                if callback: callback(int((frame_num / frame_count) * 40))
                lsbs = (frame.ravel() & 1).astype(np.uint8)
                all_frames_lsbs.append(lsbs)
                if len(all_frames_lsbs) % 10 == 0:
                    recent = np.concatenate(all_frames_lsbs[-12:])
                    if recent.tobytes().find(del_bytes) != -1:
                        found = True
                        break
                frame_num += 1
                
            cap.release()
            if not found:
                full_lsbs = np.concatenate(all_frames_lsbs)
                del_idx = full_lsbs.tobytes().find(del_bytes)
                if del_idx == -1: return False, "No hidden file found."
            else:
                full_lsbs = np.concatenate(all_frames_lsbs)
                del_idx = full_lsbs.tobytes().find(del_bytes)

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
