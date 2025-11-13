#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class DownloadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/download' or self.path == '/validate.sh':
            # Path to the validate.sh file
            file_path = '/Users/fishhead/code/mcp-security/useful-tools/validate.sh'
            
            try:
                # Read the file
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Send response with download headers
                self.send_response(200)
                self.send_header('Content-Type', 'application/x-sh')
                self.send_header('Content-Disposition', 'attachment; filename="validate.sh"')
                self.send_header('Content-Length', str(len(file_content)))
                self.end_headers()
                self.wfile.write(file_content)
                
                print(f"✓ File downloaded by {self.client_address[0]}")
                
            except FileNotFoundError:
                self.send_error(404, "validate.sh not found")
            except Exception as e:
                self.send_error(500, f"Error: {str(e)}")
        
        elif self.path == '/info':
            # Info page
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Download Server</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        max-width: 600px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #f5f5f5;
                    }
                    .container {
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    h1 { color: #333; }
                    .download-btn {
                        display: inline-block;
                        background: #007bff;
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 5px;
                        margin-top: 20px;
                    }
                    .download-btn:hover {
                        background: #0056b3;
                    }
                    code {
                        background: #f4f4f4;
                        padding: 2px 6px;
                        border-radius: 3px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📥 Download Server</h1>
                    <p>This server is running on port 8000 and serves the <code>validate.sh</code> file.</p>
                    
                    <h3>Download Options:</h3>
                    <ul>
                        <li><a href="/" class="download-btn">Download validate.sh</a></li>
                    </ul>
                    
                    <h3>Command Line:</h3>
                    <p>You can also download using curl or wget:</p>
                    <pre><code>curl -O http://localhost:8000/validate.sh</code></pre>
                    <pre><code>wget http://localhost:8000/validate.sh</code></pre>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_error(404, "Page not found. Try / for download or /info for information")
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, DownloadHandler)
    
    print("=" * 60)
    print(f"🚀 Download Server Started on Port {port}")
    print("=" * 60)
    print(f"📡 Access at: http://localhost:{port}")
    print(f"📥 Direct download: http://localhost:{port}/validate.sh")
    print(f"ℹ️  Info page: http://localhost:{port}/info")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⚠️  Server stopped")
        httpd.shutdown()

if __name__ == '__main__':
    run_server(8000)