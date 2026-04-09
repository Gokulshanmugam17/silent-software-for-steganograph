"""
Multi-Layer Steganography Module
Handles recursive hiding and extraction across different media types.
"""
import os
from typing import List, Dict, Any, Tuple, Optional
from .image_stego import ImageSteganography
from .audio_stego import AudioSteganography
from .video_stego import VideoSteganography
from .text_stego import TextSteganography

class MultiLayerSteganography:
    def __init__(self):
        self.image_stego = ImageSteganography()
        self.audio_stego = AudioSteganography()
        self.video_stego = VideoSteganography()
        self.text_stego = TextSteganography()
        
    def _get_stego_module(self, media_type: str):
        if media_type == 'image':
            return self.image_stego
        elif media_type == 'audio':
            return self.audio_stego
        elif media_type == 'video':
            return self.video_stego
        elif media_type == 'text':
            return self.text_stego
        else:
            raise ValueError(f"Unsupported media type: {media_type}")

    def hide_layers(self, layers: List[Dict[str, Any]], progress_callback=None) -> Tuple[bool, str]:
        """
        Hide data through multiple layers.
        Each layer dict should contain:
        - type: 'image', 'audio', 'video', or 'text'
        - source: path to cover media (or cover text for text type)
        - (only for first layer) text: text to hide OR secret_file: path to file
        - password: optional password
        - output: path where stego file will be saved (or output text for text type)
        """
        try:
            current_secret_path = None
            current_text = None
            
            total_layers = len(layers)
            
            for i, layer in enumerate(layers):
                if progress_callback:
                    # Outer progress: 0% to 100% split by layers
                    layer_start_progress = (i / total_layers) * 100
                    layer_end_progress = ((i + 1) / total_layers) * 100
                    def sub_callback(p):
                        actual_p = layer_start_progress + (p / 100) * (layer_end_progress - layer_start_progress)
                        progress_callback(int(actual_p))
                else:
                    sub_callback = None

                stego = self._get_stego_module(layer['type'])
                
                if i == 0:
                    # First layer: Text/File in Media or Text
                    if layer['type'] == 'text':
                        # Text steganography: hide_text(cover_text, secret_text, password)
                        # Text stego returns the stego text, not a file
                        if 'text' in layer:
                            # Use the source as cover text, text as secret
                            success, msg = stego.hide_text(
                                layer['source'],  # cover text
                                layer['text'],    # secret text
                                layer.get('password')
                            )
                            if success:
                                # For text layers, output is the stego text
                                # Store it in the layer dict for next layer
                                layer['stego_text'] = msg
                                msg = f"Text hidden in text: {len(msg)} chars"
                        else:
                            return False, "First text layer must contain 'text' to hide."
                    else:
                        # Media steganography (image, audio, video)
                        if 'text' in layer:
                            success, msg = stego.hide_text(
                                layer['source'], 
                                layer['text'], 
                                layer['output'], 
                                layer.get('password'),
                                callback=sub_callback
                            )
                        elif 'secret_file' in layer:
                            if hasattr(stego, 'hide_file'):
                                success, msg = stego.hide_file(
                                    layer['source'],
                                    layer['secret_file'],
                                    layer['output'],
                                    layer.get('password'),
                                    callback=sub_callback
                                )
                            else:
                                return False, f"Media type {layer['type']} does not support file hiding in the first layer."
                        else:
                            return False, "First layer must contain 'text' or 'secret_file'."
                else:
                    # Subsequent layers: Previous output in current source
                    prev_out = layers[i-1]['output']
                    prev_stego_text = layers[i-1].get('stego_text')
                    
                    if layer['type'] == 'text':
                        # Text layer: hide previous output (as text) in current cover text
                        if prev_stego_text:
                            # Previous layer produced text, use it as secret
                            success, msg = stego.hide_text(
                                layer['source'],  # cover text
                                prev_stego_text,  # secret text (previous stego text)
                                layer.get('password')
                            )
                            if success:
                                layer['stego_text'] = msg
                                msg = f"Text hidden in text layer {i+1}"
                        else:
                            return False, f"Layer {i+1} is text but previous layer did not produce text output."
                    else:
                        # Media layer: hide previous output file in current cover media
                        # For multi-layer, we MUST use lossless hiding to preserve the inner layer's data.
                        # hide_image/hide_video use 4MSB+4MSB which is lossy for the secret media.
                        # We use hide_file which is lossless LSB.
                        if hasattr(stego, 'hide_file'):
                            success, msg = stego.hide_file(layer['source'], prev_out, layer['output'], layer.get('password'), callback=sub_callback)
                        else:
                            # Fallback to specialized if hide_file not available
                            if layer['type'] == 'image' and prev_out.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                                success, msg = stego.hide_image(layer['source'], prev_out, layer['output'], callback=sub_callback)
                            elif layer['type'] == 'video' and prev_out.lower().endswith(('.mp4', '.avi', '.mkv')):
                                success, msg = stego.hide_video(layer['source'], prev_out, layer['output'], callback=sub_callback)
                            else:
                                return False, f"Layer {i+1} ({layer['type']}) does not support generic file hiding."

                if not success:
                    return False, f"Error at layer {i+1}: {msg}"

            if progress_callback:
                progress_callback(100)
            
            # Handle final output for text layers
            final_layer = layers[-1]
            if final_layer['type'] == 'text' and final_layer.get('stego_text'):
                return True, f"Successfully processed {total_layers} layers. Final output (text): {final_layer['stego_text'][:100]}..."
            return True, f"Successfully processed {total_layers} layers. Final output: {layers[-1]['output']}"

        except Exception as e:
            return False, f"Multi-layer hide error: {str(e)}"

    def extract_layers(self, layers: List[Dict[str, Any]], final_stego_path: str, output_dir: str, progress_callback=None) -> Tuple[bool, Any]:
        """
        Extract data back through layers.
        Layers should be in the SAME order as hiding. Logic will reverse it.
        """
        try:
            # We work backwards
            current_stego = final_stego_path
            current_layer_index = len(layers) - 1
            
            total_layers = len(layers)
            
            while current_layer_index >= 0:
                layer = layers[current_layer_index]
                
                if progress_callback:
                    layer_start_progress = ((total_layers - 1 - current_layer_index) / total_layers) * 100
                    layer_end_progress = ((total_layers - current_layer_index) / total_layers) * 100
                    def sub_callback(p):
                        actual_p = layer_start_progress + (p / 100) * (layer_end_progress - layer_start_progress)
                        progress_callback(int(actual_p))
                else:
                    sub_callback = None

                stego = self._get_stego_module(layer['type'])
                
                if current_layer_index == 0:
                    # Final extraction (original text or file)
                    if 'text' in layer or 'is_text' in layer:
                        success, result = stego.extract_text(current_stego, layer.get('password'), callback=sub_callback)
                        return success, result
                    else:
                        # Extract as file
                        success, result = stego.extract_file(current_stego, output_dir, layer.get('password'), callback=sub_callback)
                        return success, result
                else:
                    # Intermediate extraction
                    # We use extract_file as we used hide_file for intermediate layers
                    if hasattr(stego, 'extract_file'):
                        success, result = stego.extract_file(current_stego, output_dir, layer.get('password'), callback=sub_callback)
                        if success:
                            # Parse result: "Extracted to path"
                            import re
                            match = re.search(r"Extracted to (.*)", result)
                            if match:
                                temp_output = match.group(1).strip()
                            else:
                                return False, f"Could not determine extracted file path from: {result}"
                            msg = result
                        else:
                            return False, f"Error extracting layer {current_layer_index+1}: {result}"
                    else:
                        # Fallback for specialized (though we prefer hide_file/extract_file now)
                        temp_output = os.path.join(output_dir, f"temp_layer_{current_layer_index}")
                        is_specialized = False
                        if layer['type'] == 'image' and layers[current_layer_index-1]['type'] == 'image':
                            temp_output += ".png"
                            success, msg = stego.extract_image(current_stego, temp_output, callback=sub_callback)
                            is_specialized = True
                        elif layer['type'] == 'video' and layers[current_layer_index-1]['type'] == 'video':
                            temp_output += ".avi"
                            success, msg = stego.extract_video(current_stego, temp_output, callback=sub_callback)
                            is_specialized = True
                        
                        if not is_specialized:
                            return False, f"Layer {current_layer_index+1} ({layer['type']}) does not support generic file extraction."
                        if not success:
                            return False, f"Error extracting layer {current_layer_index+1}: {msg}"
                    
                    current_stego = temp_output
                    current_layer_index -= 1

            if progress_callback:
                progress_callback(100)
            return True, "Extraction completed."

        except Exception as e:
            return False, f"Multi-layer extract error: {str(e)}"

    def auto_extract_layers(self, initial_stego_path: str, passwords: List[str], output_dir: str, progress_callback=None) -> Tuple[bool, Any, int]:
        """
        Automatically identifies layers and extracts them.
        Returns: (success, result_data, layers_count)
        result_data is a dict: {'final': final_data, 'intermediates': [path1, path2]}
        """
        try:
            current_stego = initial_stego_path
            layers_found = 0
            intermediates = []
            
            # Passwords might be provided as a list. We'll use them in order.
            # If not enough passwords, we'll try None.
            
            while True:
                # Identify media type
                ext = os.path.splitext(current_stego)[1].lower()
                m_type = None
                if ext in ['.png', '.bmp', '.tiff', '.tif']: m_type = 'image'
                elif ext in ['.wav']: m_type = 'audio'
                elif ext in ['.avi', '.mp4', '.mkv', '.mov']: m_type = 'video'
                
                if not m_type:
                    return False, f"Unsupported file extension: {ext}", layers_found

                stego = self._get_stego_module(m_type)
                current_pw = passwords[layers_found] if layers_found < len(passwords) else None
                
                # Progress simulation for the current layer
                if progress_callback:
                    progress_callback(min(95, layers_found * 30 + 10))

                # Attempt 1: Extract as File (Intermediate or final file)
                success, result = stego.extract_file(current_stego, output_dir, current_pw)
                
                if success:
                    # result is "Extracted to path"
                    import re
                    match = re.search(r"Extracted to (.*)", result)
                    if match:
                        extracted_path = match.group(1).strip()
                        layers_found += 1
                        
                        # Check if extracted file is another layer
                        inner_ext = os.path.splitext(extracted_path)[1].lower()
                        if inner_ext in ['.png', '.bmp', '.wav', '.avi', '.mp4', '.mkv']:
                            # It COULD be another layer, but we need to check if it actually contains something
                            # We'll try to extract from it in the next iteration
                            intermediates.append(extracted_path)
                            current_stego = extracted_path
                            continue
                        else:
                            # It's a non-stego file or original secret file
                            return True, {'final': extracted_path, 'intermediates': intermediates}, layers_found
                    else:
                        return False, "Unexpected result format from extract_file", layers_found
                
                # Attempt 2: Extract as Text (Final layer or mis-extracted file)
                success, result = stego.extract_text(current_stego, current_pw)
                if success:
                    # HEURISTIC: Check if this "text" is actually a mis-extracted file
                    # (This happens if extract_file failed but extract_text found the delimiter)
                    if isinstance(result, str) and result.startswith('{{FILE:'):
                        import re
                        match = re.search(r"{{FILE:(.+?),SIZE:(\d+)}}", result)
                        if match:
                            filename = match.group(1)
                            header_end = result.find('}}') + 2
                            file_data_str = result[header_end:]
                            
                            # Convert back to bytes (since it was extracted as text)
                            # This is tricky because extract_text might have used 'ignore' or 'replace'
                            # But if it's a lossless AVI, it might be okay.
                            try:
                                # We try our best to recover the bytes
                                file_content = file_data_str.encode('utf-8', errors='ignore')
                                extracted_path = os.path.join(output_dir, filename)
                                with open(extracted_path, 'wb') as f:
                                    f.write(file_content)
                                
                                layers_found += 1
                                intermediates.append(extracted_path)
                                current_stego = extracted_path
                                continue
                            except:
                                pass # Fall back to treating as text

                    # If this succeeds and not a file, it's definitely text data
                    layers_found += 1
                    return True, {'final': result, 'intermediates': intermediates}, layers_found
                
                # If we were processing intermediates and suddenly can't find anything more,
                # the "current_stego" (which was the last extracted file) is the final one.
                if layers_found > 0 and intermediates:
                    final_file = intermediates.pop() # Remove from intermediates as it's the final
                    return True, {'final': final_file, 'intermediates': intermediates}, layers_found

                return False, f"Could not identify hidden data in layer {layers_found + 1}", layers_found

        except Exception as e:
            return False, f"Auto-layer extract error: {str(e)}", 0
