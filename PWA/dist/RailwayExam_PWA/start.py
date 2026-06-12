"""Simple dev server for the Railway Exam PWA.

Usage: python start.py [port]
Default port: 8080

This is ONLY needed for local development/testing. For production,
deploy the entire pwa/ folder to any static hosting service.
"""
import sys
import os
import webbrowser
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

# Switch to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add proper MIME types for manifest and service worker
SimpleHTTPRequestHandler.extensions_map.update({
    '.json': 'application/json',
    '.manifest': 'application/manifest+json',
})

print(f"Railway Exam PWA server starting...")
print(f"Open http://127.0.0.1:{PORT} in your browser")
print(f"Press Ctrl+C to stop.")

# Auto-open browser
def open_browser():
    time.sleep(0.8)
    webbrowser.open(f"http://127.0.0.1:{PORT}")

threading.Thread(target=open_browser, daemon=True).start()

httpd = HTTPServer(("127.0.0.1", PORT), SimpleHTTPRequestHandler)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    httpd.server_close()
