#!/usr/bin/env python3
import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000
FILE = "json-viewer.html"

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = FILE
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def main():
    # Change to directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if not os.path.exists(FILE):
        print(f"Error: {FILE} not found in current directory.")
        sys.exit(1)

    print(f"Starting JSON Viewer server at http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    
    # Open browser automatically
    webbrowser.open(f"http://localhost:{PORT}")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()