"""
SILENT - Secure Information Layering Engine for Non-Traceable Transmission
"""
import os
import sys
import webbrowser
import threading
import time

def main():
    """Launch the SILENT web application."""
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import Flask app
    from web_app.app import app
    
    # Configuration
    host = '127.0.0.1'
    port = 8080
    url = f'http://{host}:{port}'
    
    print("""
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
    ║   🌐 Web Interface: {:<40} ║
    ║                                                              ║
    ║   Press Ctrl+C to stop the server                            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """.format(url))
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run Flask app
    try:
        app.run(host=host, port=port, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n    Server stopped. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
