from flask import Flask, render_template, request, send_file, jsonify, session, redirect, url_for
import os
import json
import sys
import shutil
import time
import base64
import zipfile
from io import BytesIO
import hashlib
from functools import wraps

# Try to import from cryptography package
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    USE_CRYPTOGRAPHY = True
except ImportError:
    try:
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
        USE_CRYPTOGRAPHY = False
    except ImportError:
        from Cryptodome.Cipher import AES
        from Cryptodome.Random import get_random_bytes
        USE_CRYPTOGRAPHY = False

# Add parent directory to path to import steganography modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from steganography.image_stego import ImageSteganography
from steganography.audio_stego import AudioSteganography
from steganography.video_stego import VideoSteganography
from steganography.text_stego import TextSteganography
from steganography.multi_layer_stego import MultiLayerSteganography

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
app.secret_key = 'silent_secret_key_access_2024_hari' # Change this in production

# Load authorized users from JSON file
def load_users():
    # Get absolute path to the root directory where users.json is located
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'users.json')
    
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                return json.load(f)
        else:
            print(f"DEBUG: users.json not found at {json_path}")
            return {"Hari": "silent@2024"}
    except Exception as e:
        print(f"DEBUG: Error loading users.json: {e}")
        return {"Hari": "silent@2024"}

ALLOWED_USERS = load_users()

# History Management
HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'history.json')

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"Error saving history: {e}")

def add_to_history(username, operation, media_type, status="Success", result=""):
    history = load_history()
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "user": username,
        "operation": operation,
        "media_type": media_type,
        "status": status,
        "result": result
    }
    history.insert(0, entry)  # Add to top
    save_history(history[:50])  # Keep last 50 entries

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize modules
stego_modules = {
    'text': TextSteganography(),
    'image': ImageSteganography(),
    'audio': AudioSteganography(),
    'video': VideoSteganography()
}

multi_layer_stego = MultiLayerSteganography()

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Reload users to get latest changes from JSON
        users = load_users()
        
        # Strip whitespace from inputs
        username_input = request.form.get('username', '').strip()
        password_input = request.form.get('password', '').strip()
        
        print(f"DEBUG: Login Attempt - User: '{username_input}'")
        
        # Check credentials (case-insensitive username check for better UX)
        # We look for a match where key.lower() == input.lower()
        matched_user = None
        for u in users:
            if u.lower() == username_input.lower():
                matched_user = u
                break
        
        if matched_user and str(users[matched_user]) == password_input:
            print(f"DEBUG: Login Success for {matched_user}")
            session['logged_in'] = True
            session['username'] = matched_user
            return redirect(url_for('index'))
        else:
            print(f"DEBUG: Login Failed for '{username_input}'")
            return render_template('login.html', error="Invalid credentials. Access restricted.")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))

@app.route('/api/history')
@login_required
def get_history():
    return jsonify(load_history())

@app.route('/api/clear_history', methods=['POST'])
@login_required
def clear_history():
    save_history([])
    return jsonify({'success': True})

@app.route('/process', methods=['POST'])
@login_required
def process():
    try:
        # Get operation details
        operation = request.form.get('operation')  # 'hide' or 'extract'
        media_type = request.form.get('media_type') # 'text', 'image', 'audio', 'video'
        data_type = request.form.get('data_type')   # 'text' or 'media'
        password = request.form.get('password')
        text_data = request.form.get('text_data')

        if not operation or not media_type:
            return jsonify({'error': 'Missing operation or media type'}), 400

        # Get additional parameters
        try:
            expiry_hours = float(request.form.get('expiry_hours', 0))
        except:
            expiry_hours = 0
            
        decoy_on_fail = 'decoy_on_fail' in request.form

        # Special handling for text-to-text steganography (NO FILE REQUIRED)
        if media_type == 'text':
            stego = stego_modules.get(media_type)
            if not stego:
                return jsonify({'error': 'Text module not found'}), 400

            if operation == 'hide':
                # Text-to-text steganography (HIDE)
                cover_text = request.form.get('cover_text')
                if not cover_text or not text_data:
                    return jsonify({'error': 'Cover text and secret message required'}), 400
                success, stego_text = stego.hide_text(cover_text, text_data, password, expiry_hours=expiry_hours)
                
                if success:
                    add_to_history(session.get('username'), 'Hide', 'Text', 'Success', 'Message Hidden')
                    return jsonify({'success': True, 'message': 'Text hidden successfully', 'data': stego_text})
                else:
                    return jsonify({'success': False, 'message': stego_text})
            
            elif operation == 'extract':
                # Text-to-text steganography (EXTRACT)
                stego_text = request.form.get('stego_text')
                if not stego_text:
                    return jsonify({'error': 'Stego text required'}), 400
                success, result = stego.extract_text(stego_text, password, decoy_on_fail=decoy_on_fail)
                
                if success:
                    add_to_history(session.get('username'), 'Extract', 'Text', 'Success', 'Message Extracted')
                    return jsonify({'success': True, 'message': 'Text extracted successfully', 'data': result})
                else:
                    return jsonify({'success': False, 'message': result})

        # For other media types (image, audio, video) - FILE REQUIRED
        # Handle file uploads
        if 'source_file' not in request.files:
            return jsonify({'error': 'No source file provided'}), 400
        
        source_file = request.files['source_file']
        if source_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Save source file
        source_path = os.path.join(app.config['UPLOAD_FOLDER'], source_file.filename)
        source_file.save(source_path)

        # Prepare output path
        output_filename = f"output_{source_file.filename}"
        if media_type == 'video' and not output_filename.endswith('.avi'):
             output_filename = os.path.splitext(output_filename)[0] + ".avi"
        elif media_type == 'audio' and not output_filename.endswith('.wav'):
             output_filename = os.path.splitext(output_filename)[0] + ".wav"
        elif media_type == 'image' and not output_filename.endswith('.png'):
             output_filename = os.path.splitext(output_filename)[0] + ".png"

        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Get module
        stego = stego_modules.get(media_type)
        if not stego:
            return jsonify({'error': 'Invalid media type'}), 400

        msg = "Processing complete"
        success = False

        if operation == 'hide':
            if data_type == 'text':
                if not text_data:
                    return jsonify({'error': 'No text provided'}), 400
                success, msg = stego.hide_text(source_path, text_data, output_path, password, expiry_hours=expiry_hours)
            
            elif data_type == 'media':
                if 'media_file' not in request.files:
                     return jsonify({'error': 'No secret media file provided'}), 400
                secret_file = request.files['media_file']
                secret_path = os.path.join(app.config['UPLOAD_FOLDER'], secret_file.filename)
                secret_file.save(secret_path)

                if media_type == 'image':
                    ext = os.path.splitext(secret_file.filename)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
                        success, msg = stego.hide_image(source_path, secret_path, output_path)
                    else:
                        success, msg = stego.hide_file(source_path, secret_path, output_path, password)

                elif media_type == 'audio':
                    ext = os.path.splitext(secret_file.filename)[1].lower()
                    if ext in ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.mpeg', '.aac', '.wma', '.aiff']:
                        success, msg = stego.hide_audio(source_path, secret_path, output_path, password)
                    else:
                        success, msg = stego.hide_file(source_path, secret_path, output_path, password)
                        
                elif media_type == 'video':
                    ext = os.path.splitext(secret_file.filename)[1].lower()
                    if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                        success, msg = stego.hide_video(source_path, secret_path, output_path)
                    else:
                        success, msg = stego.hide_file(source_path, secret_path, output_path, password)
        
        elif operation == 'extract':
            if media_type == 'text':
                # Text-to-text extraction
                stego_text = request.form.get('stego_text')
                if not stego_text:
                    return jsonify({'error': 'Stego text required'}), 400
                success, result = stego.extract_text(stego_text, password, decoy_on_fail=decoy_on_fail)
                
                if success:
                    add_to_history(session.get('username'), 'Extract', 'Text', 'Success', 'Message Extracted')
                    return jsonify({'success': True, 'message': 'Text extracted successfully', 'data': result})
                else:
                    return jsonify({'success': False, 'message': result})
            
            # AUTOMATIC DETECTION FOR ALL MEDIA TYPES (Smart Extraction)
            # For image media, we prioritize text extraction first (most common use case)
            # Then try file extraction, then media extraction
            
            extracted_filename = f"extracted_{source_file.filename}"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], extracted_filename)
            
            # --- PHASE 1: Try Lossless LSB Text Extraction FIRST (most common for text-in-image) ---
            success, result = stego.extract_text(source_path, password, decoy_on_fail=decoy_on_fail)
            if success:
                add_to_history(session.get('username'), 'Extract', media_type.capitalize(), 'Success', 'Message Extracted')
                return jsonify({'success': True, 'message': 'Text extracted successfully', 'data': result})
            elif "Security Triggered" in result or "Dead-Man" in result:
                # Critical security triggers should stop everything
                return jsonify({'success': False, 'message': result})
            elif ("Decryption failed" in result or "Incorrect Password" in result) and media_type == 'text':
                # Only stop if we are SURE it was supposed to be text
                return jsonify({'success': False, 'message': result})
            
            # --- PHASE 2: Try Lossless LSB File Extraction ---
            success, msg = stego.extract_file(source_path, app.config['UPLOAD_FOLDER'], password)
            if success:
                import re
                match = re.search(r"Extracted to (.+)$", msg)
                if match:
                    output_path = match.group(1)
                    add_to_history(session.get('username'), 'Extract', media_type.capitalize(), 'Success', 'File Extracted')
                    return jsonify({'success': True, 'message': 'File detected and extracted successfully', 'download_url': f'/download/{os.path.basename(output_path)}', 'filename': os.path.basename(output_path), 'is_file': True})
            elif "Incorrect Password" in msg or "Decryption failed" in msg:
                return jsonify({'success': False, 'message': msg})

            # --- PHASE 3: Try Specialized Media Extraction (Audio/Video/Image Merge) ---
            if media_type == 'image':
                success, msg = stego.extract_image(source_path, output_path)
            elif media_type == 'audio':
                success, msg = stego.extract_audio(source_path, output_path, password)
            elif media_type == 'video':
                success, msg = stego.extract_video(source_path, output_path)
            
            if success:
                add_to_history(session.get('username'), 'Extract', media_type.capitalize(), 'Success', 'Media Extracted')
                return jsonify({'success': True, 'message': 'Hidden media extracted successfully', 'download_url': f'/download/{os.path.basename(output_path)}', 'filename': os.path.basename(output_path), 'is_file': True})
            else:
                return jsonify({'success': False, 'message': 'Smart Extract failed: No hidden data detected or incorrect password.'})

        if success:
            add_to_history(session.get('username'), operation.capitalize(), media_type.capitalize(), 'Success', msg if isinstance(msg, str) and len(msg) < 50 else 'File Processed')
            return jsonify({'success': True, 'message': msg, 'download_url': f'/download/{os.path.basename(output_path)}', 'filename': os.path.basename(output_path), 'is_file': True})
        else:
            return jsonify({'success': False, 'message': msg})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route('/cleanup', methods=['POST'])
@login_required
def cleanup():
    # Clean up uploads folder
    try:
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/multilayer', methods=['POST'])
@login_required
def multilayer():
    try:
        operation = request.form.get('operation')  # 'hide' or 'extract'
        
        if operation == 'hide':
            # Get layers configuration
            data_type = request.form.get('data_type', 'text')
            secret_text = request.form.get('secret_text')
            layer1_type = request.form.get('layer1_type')
            layer2_type = request.form.get('layer2_type')
            layer1_password = request.form.get('layer1_password')
            layer2_password = request.form.get('layer2_password')
            
            secret_file_path = None
            if data_type == 'media':
                if 'secret_file' not in request.files:
                    return jsonify({'error': 'Secret file required for media type'}), 400
                secret_f = request.files['secret_file']
                secret_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secret_f.filename)
                secret_f.save(secret_file_path)
            elif not secret_text:
                return jsonify({'error': 'Secret message required for text type'}), 400
            
            # Handle layer 1 - can be file or text
            if layer1_type == 'text':
                layer1_text = request.form.get('layer1_text')
                if not layer1_text:
                    return jsonify({'error': 'Layer 1 text is required for text type'}), 400
                layer1_source = layer1_text
            else:
                if 'layer1_cover' not in request.files:
                    return jsonify({'error': 'Layer 1 cover file required'}), 400
                layer1_file = request.files['layer1_cover']
                layer1_source = os.path.join(app.config['UPLOAD_FOLDER'], layer1_file.filename)
                layer1_file.save(layer1_source)
            
            # Handle layer 2 - can be file or text
            if layer2_type == 'text':
                layer2_text = request.form.get('layer2_text')
                if not layer2_text:
                    return jsonify({'error': 'Layer 2 text is required for text type'}), 400
                layer2_source = layer2_text
            else:
                if 'layer2_cover' not in request.files:
                    return jsonify({'error': 'Layer 2 cover file required'}), 400
                layer2_file = request.files['layer2_cover']
                layer2_source = os.path.join(app.config['UPLOAD_FOLDER'], layer2_file.filename)
                layer2_file.save(layer2_source)
            
            if not layer1_type or not layer2_type:
                return jsonify({'error': 'Missing required parameters'}), 400
            
            # Prepare outputs based on layer types
            ext1 = 'txt' if layer1_type == 'text' else ('png' if layer1_type == 'image' else 'wav' if layer1_type == 'audio' else 'avi')
            ext2 = 'txt' if layer2_type == 'text' else ('png' if layer2_type == 'image' else 'wav' if layer2_type == 'audio' else 'avi')
            
            temp_output = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_layer1.{ext1}')
            final_output = os.path.join(app.config['UPLOAD_FOLDER'], f'multilayer_output.{ext2}')
            
            # Build layers config
            layer1_dict = {
                'type': layer1_type,
                'source': layer1_source,
                'output': temp_output,
                'password': layer1_password if layer1_password else None
            }
            
            if data_type == 'text':
                layer1_dict['text'] = secret_text
            else:
                layer1_dict['secret_file'] = secret_file_path
                
            layers = [
                layer1_dict,
                {
                    'type': layer2_type,
                    'source': layer2_source,
                    'output': final_output,
                    'password': layer2_password if layer2_password else None
                }
            ]
            
            # Process
            print(f"DEBUG: Starting multi-layer hide with {len(layers)} layers")
            success, msg = multi_layer_stego.hide_layers(layers)
            print(f"DEBUG: Multi-layer hide success: {success}, msg: {msg}")
            
            # Check if final layer is text type
            final_layer = layers[-1]
            is_text_output = final_layer['type'] == 'text'
            
            # Cleanup temp only for non-text layers
            if not is_text_output and os.path.exists(temp_output):
                os.remove(temp_output)
            
            if success:
                add_to_history(session.get('username'), 'Hide', 'Multi-Layer', 'Success', 'Layered Multi-Media')
                
                if is_text_output:
                    stego_text = final_layer.get('stego_text', msg)
                    return jsonify({
                        'success': True,
                        'message': msg,
                        'data': stego_text,
                        'is_file': False
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': msg,
                        'download_url': f'/download/{os.path.basename(final_output)}'
                    })
            else:
                return jsonify({'success': False, 'message': msg})
        
        elif operation == 'extract':
            # Always use auto-identify logic now
            data_type = request.form.get('data_type', 'text')
            
            # Handle stego file
            if 'stego_file' in request.files and request.files['stego_file'].filename:
                stego_file = request.files['stego_file']
                stego_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_file.filename)
                stego_file.save(stego_path)
            else:
                stego_path = request.form.get('stego_text')
                if not stego_path:
                    return jsonify({'error': 'Stego file or text required'}), 400

            # Collect passwords from individual fields
            pass_1 = request.form.get('auto_pass_1', '').strip()
            pass_2 = request.form.get('auto_pass_2', '').strip()
            pass_list = []
            if pass_1: pass_list.append(pass_1)
            if pass_2: pass_list.append(pass_2)
            
            # Use auto_extract_layers
            success, result_data, count = multi_layer_stego.auto_extract_layers(stego_path, pass_list, app.config['UPLOAD_FOLDER'])
            
            # Result already obtained above
            
            if success:
                add_to_history(session.get('username'), 'Extract', 'Multi-Layer', 'Success', 'Layers Unwound')
                
                # Parse result_data
                # result_data is {'final': ..., 'intermediates': [...]}
                final_res = result_data['final']
                intermediates = result_data['intermediates']
                
                is_file = False
                if isinstance(final_res, str) and os.path.isabs(final_res) and os.path.exists(final_res):
                    is_file = True
                
                display_text = f"File extracted: {os.path.basename(final_res)}" if is_file else final_res
                
                # Prepare intermediate URLs
                inter_urls = []
                for p in intermediates:
                    inter_urls.append(f'/download/{os.path.basename(p)}')
                
                return jsonify({
                    'success': True,
                    'message': 'Data extracted successfully',
                    'data': display_text,
                    'raw_data': final_res if not is_file else None,
                    'is_file': is_file,
                    'download_url': f'/download/{os.path.basename(final_res)}' if is_file else None,
                    'intermediates': inter_urls,
                    'cover_url': f'/download/{os.path.basename(stego_path)}'
                })
            else:
                return jsonify({'success': False, 'message': result_data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Listen on Render's assigned port, or default to 8080 locally
    port = int(os.environ.get("PORT", 8080))
    # In production, debug should be False
    app.run(host='0.0.0.0', port=port, debug=False)
