"""
SILENT - Secure Information Layering Engine for Non-Traceable Transmission
"""
import os
import sys
import webbrowser
import threading
import time
import io
import socket
import atexit

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def wait_for_port(port, timeout=30):
    """Wait for port to be available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False

def main():
    """Launch the SILENT web application."""
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import Flask app
    from web_app.app import app
    
    # Configuration
    host = '127.0.0.1'
    
    # Allow port to be specified as command line argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    else:
        port = 8080
    
    url = f'http://127.0.0.1:{port}'
    
    # Check if port is in use and wait for it
    if is_port_in_use(port):
        print(f"\nWARNING: Port {port} is already in use!")
        print("Waiting for port to be available...")
        if not wait_for_port(port, timeout=10):
            print(f"ERROR: Could not free port {port}. Try using a different port.")
            print(f"Usage: python main.py <port>")
            print(f"Example: python main.py 8081")
            input("\nPress Enter to exit...")
            sys.exit(1)
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   ███████╗██╗██╗     ███████╗███╗   ██╗████████╗            ║
    ║   ██╔════╝██║██║     ██╔════╝████╗  ██║╚══██╔══╝            ║
    ║   ███████╗██║██║     █████╗  ██╔██╗ ██║   ██║               ║
    ║   ╚════██║██║██║     ██╔══╝  ██║╚██╗██║   ██║               ║
    ║   ███████║██║███████╗███████╗██║ ╚████║   ██║               ║
    ║   ╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝               ║
    ║                                                              ║
    ║   Secure Information Layering Engine for                     ║
    ║   Non-Traceable Transmission                                 ║
    ║                                                              ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║   🌐 Web Interface: {url:<40} ║
    ║                                                              ║
    ║   Press Ctrl+C to stop the server                            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Open browser after server is ready
    def open_browser():
        # Wait longer for server to be fully ready
        time.sleep(3)
        webbrowser.open(url)
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run Flask app with threaded=True to handle multiple connections
    try:
        print("\nStarting Flask server...")
        app.run(host='127.0.0.1', port=port, debug=True, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"\nError starting server: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        print("\n\n    Server stopped. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
