
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

logger = logging.getLogger('BotAutomation.KeepAlive')

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        # Suppress logging of HTTP requests
        return

def run_server():
    server_address = ('0.0.0.0', 8080)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    logger.info(f"Starting keep-alive server on port 8080")
    httpd.serve_forever()

def start_server():
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True  # So the thread will exit when the main process exits
    server_thread.start()
    return server_thread
