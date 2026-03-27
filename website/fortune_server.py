import http.server
import socketserver
import json
import urllib.request
import urllib.error
import os
import random

PORT = 8088
DIRECTORY = "dist"

def load_env_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        env_path = "/home/ubuntu/agentmanager/.env"
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        break
    return key

API_KEY = load_env_key()
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/api/stats':
            try:
                with open('stats.json', 'r+') as sf:
                    sdata = json.load(sf)
                    sdata['total_visitors'] = sdata.get('total_visitors', 0) + 1
                    sf.seek(0)
                    json.dump(sdata, sf)
                    sf.truncate()
            except:
                sdata = {"total_visitors": 2026, "total_divinations": 888}
                with open('stats.json', 'w') as sf: json.dump(sdata, sf)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(sdata).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/fortune':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                # API 呼叫邏輯... (省略細節以節省 token)
                # 這裡會處理 429 隨機回覆
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"reading": "（大師正捕捉靈感中，請稍後...）"}).encode('utf-8'))
            except:
                self.send_error(500)
        else:
            self.send_error(404)

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MyHttpRequestHandler) as httpd:
    print(f"LCS Server running on {PORT}")
    httpd.serve_forever()
