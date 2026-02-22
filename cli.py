"""
Command-line interface for Steganography Tool
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from steganography.image_stego import ImageSteganography
from steganography.audio_stego import AudioSteganography
from steganography.video_stego import VideoSteganography
from steganography.multi_layer_stego import MultiLayerSteganography


def progress_callback(percent):
    bar_length = 40
    filled = int(bar_length * percent / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f'\rProgress: [{bar}] {percent}%', end='', flush=True)
    if percent >= 100:
        print()


def main():
    parser = argparse.ArgumentParser(
        description="SILENT (Secure Information Layering Engine for Non-Traceable Transmission)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Hide command
    hide_parser = subparsers.add_parser('hide', help='Hide text in a file')
    hide_parser.add_argument('type', choices=['image', 'audio', 'video'], help='Media type')
    hide_parser.add_argument('source', help='Source file path')
    hide_parser.add_argument('output', help='Output file path')
    hide_parser.add_argument('-t', '--text', help='Text to hide')
    hide_parser.add_argument('-f', '--file', help='File containing text to hide')
    hide_parser.add_argument('-p', '--password', help='Encryption password')
    hide_parser.add_argument('-m', '--media-file', help='Media file to hide (image/audio/video)')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract hidden text')
    extract_parser.add_argument('type', choices=['image', 'audio', 'video'], help='Media type')
    extract_parser.add_argument('source', help='Stego file path')
    extract_parser.add_argument('-o', '--output', help='Output file for extracted text/media')
    extract_parser.add_argument('-p', '--password', help='Decryption password')
    extract_parser.add_argument('-m', '--media', action='store_true', help='Extract hidden media')
    
    # Multi-layer command
    ml_parser = subparsers.add_parser('multilayer', help='Multi-layer steganography (e.g., text -> image -> video)')
    ml_subparsers = ml_parser.add_subparsers(dest='ml_command', help='Multi-layer commands')
    
    ml_hide = ml_subparsers.add_parser('hide', help='Hide data through multiple layers')
    ml_hide.add_argument('--text', required=True, help='Secret text to hide')
    ml_hide.add_argument('--layers', required=True, help='Comma-separated media types (e.g., image,video)')
    ml_hide.add_argument('--covers', required=True, help='Comma-separated cover file paths')
    ml_hide.add_argument('--outputs', required=True, help='Comma-separated output file paths')
    ml_hide.add_argument('--passwords', help='Comma-separated passwords for each layer')

    ml_extract = ml_subparsers.add_parser('extract', help='Extract data from multi-layer stego')
    ml_extract.add_argument('--source', required=True, help='Final stego file path')
    ml_extract.add_argument('--layers', required=True, help='Comma-separated media types in hiding order')
    ml_extract.add_argument('--output-dir', required=True, help='Directory to save extracted data')
    ml_extract.add_argument('--passwords', help='Comma-separated passwords')

    # Info command
    info_parser = subparsers.add_parser('info', help='Get file information')
    info_parser.add_argument('type', choices=['image', 'audio', 'video'], help='Media type')
    info_parser.add_argument('file', help='File to analyze')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize modules
    modules = {
        'image': ImageSteganography(),
        'audio': AudioSteganography(),
        'video': VideoSteganography()
    }
    
    if args.command in ['info', 'hide', 'extract']:
        stego = modules[args.type]
    
    if args.command == 'info':
        try:
            info_methods = {'image': 'get_image_info', 'audio': 'get_audio_info', 'video': 'get_video_info'}
            info = getattr(stego, info_methods[args.type])(args.file)
            print(f"\n📊 File Information: {args.file}\n")
            for key, value in info.items():
                print(f"  {key}: {value}")
            print()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif args.command == 'hide':
        if args.media_file:
            # Hide media
            print(f"\n🔒 Hiding {args.type} in {args.type}...")
            if args.type == 'image':
                success, msg = stego.hide_image(args.source, args.media_file, args.output, progress_callback)
            elif args.type == 'audio':
                success, msg = stego.hide_audio(args.source, args.media_file, args.output, progress_callback)
            elif args.type == 'video':
                success, msg = stego.hide_video(args.source, args.media_file, args.output, progress_callback)
            print(f"{'✅' if success else '❌'} {msg}")
        else:
            if not args.text and not args.file:
                print("❌ Error: Provide text with -t, a text file with -f, or a media file with -m")
                return
            
            text = args.text if args.text else open(args.file, 'r').read()
            print(f"\n🔒 Hiding text in {args.type}...")
            success, msg = stego.hide_text(args.source, text, args.output, args.password, progress_callback)
            print(f"{'✅' if success else '❌'} {msg}")
    
    elif args.command == 'extract':
        if args.media:
            print(f"\n🔓 Extracting {args.type} from {args.type}...")
            if args.type == 'image':
                success, msg = stego.extract_image(args.source, args.output, progress_callback)
            elif args.type == 'audio':
                success, msg = stego.extract_audio(args.source, args.output, progress_callback)
            elif args.type == 'video':
                success, msg = stego.extract_video(args.source, args.output, progress_callback)
            print(f"{'✅' if success else '❌'} {msg}")
        else:
            print(f"\n🔓 Extracting text from {args.type}...")
            success, result = stego.extract_text(args.source, args.password, progress_callback)
            if success:
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(result)
                    print(f"✅ Text saved to {args.output}")
                else:
                    print(f"\n📝 Extracted Text:\n{'-'*40}\n{result}\n{'-'*40}")
            else:
                print(f"❌ {result}")

    elif args.command == 'multilayer':
        ml = MultiLayerSteganography()
        if args.ml_command == 'hide':
            layer_types = args.layers.split(',')
            covers = args.covers.split(',')
            outputs = args.outputs.split(',')
            passwords = args.passwords.split(',') if args.passwords else [None] * len(layer_types)
            
            if not (len(layer_types) == len(covers) == len(outputs)):
                print("❌ Error: layers, covers, and outputs must have same number of items.")
                return
            
            layers_config = []
            for i in range(len(layer_types)):
                config = {
                    'type': layer_types[i].strip(),
                    'source': covers[i].strip(),
                    'output': outputs[i].strip(),
                    'password': passwords[i].strip() if i < len(passwords) and passwords[i] else None
                }
                if i == 0:
                    config['text'] = args.text
                layers_config.append(config)
            
            print(f"\n🔒 processing {len(layers_config)} layers...")
            success, msg = ml.hide_layers(layers_config, progress_callback)
            print(f"{'✅' if success else '❌'} {msg}")
            
        elif args.ml_command == 'extract':
            layer_types = args.layers.split(',')
            passwords = args.passwords.split(',') if args.passwords else [None] * len(layer_types)
            
            layers_config = []
            for i in range(len(layer_types)):
                layers_config.append({
                    'type': layer_types[i].strip(),
                    'password': passwords[i].strip() if i < len(passwords) and passwords[i] else None,
                    'is_text': (i == 0)
                })
            
            print(f"\n🔓 extracting from {len(layers_config)} layers...")
            success, result = ml.extract_layers(layers_config, args.source, args.output_dir, progress_callback)
            if success:
                print(f"\n📝 Result: {result}")
            else:
                print(f"❌ {result}")


if __name__ == "__main__":
    main()
