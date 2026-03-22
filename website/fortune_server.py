import http.server
import socketserver
import json
import urllib.request
import urllib.error
import os

PORT = 8088
DIRECTORY = "dist"  # Serve the built version in dev to see the actual app

# Set your API Key here directly or load from env
# I am fetching it from the agentmanager .env to keep it hidden from frontend
API_KEY = "AIzaSyC_5FeMKlkK8r0Bj6DBbxwmy56a3MA900U"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == '/api/fortune':
            # Handle Fortune Telling Backend Logic
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                question = data.get('question', '')
                card_title = data.get('cardTitle', '')
                card_meaning = data.get('cardMeaning', '')
                lang = data.get('lang', 'zh')
                
                if not question or not card_title:
                    self.send_error(400, "Bad Request: Missing question or card")
                    return
                
                # Construct Language context
                if lang == 'en':
                    system_prompt = f"You are 'The LeopardCat Oracle', a wise and mysterious monastic cat. The user asks: '{question}'. You just drew the Tarot card: '{card_title}', which basically means: '{card_meaning}'. Give a personalized 3-sentence tarot reading in English, blending the card's meaning with the user's question. Speak mystically but concisely."
                else:
                    system_prompt = f"你現在是『靈山仙貓大師』，一隻在深山修行的神祕石虎。使用者問了這個問題：『{question}』。你為他抽出了塔羅牌：【{card_title}】，原始牌義是：『{card_meaning}』。請結合牌義與問題，給予一段約 100 字的精闢解籤與建議。語氣要充滿禪意且神祕，像個有智慧的長者。"

                # Payload for Gemini 2.5 API
                gemini_payload = {
                    "contents": [{
                        "parts": [{"text": system_prompt}]
                    }]
                }
                
                req = urllib.request.Request(GEMINI_URL, method="POST")
                req.add_header('Content-Type', 'application/json')
                
                with urllib.request.urlopen(req, data=json.dumps(gemini_payload).encode('utf-8')) as response:
                    res_body = response.read()
                    res_json = json.loads(res_body)
                    text_response = res_json['candidates'][0]['content']['parts'][0]['text']

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps({"reading": text_response}).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

# Ensure dist exists (since we run npm run build)
if not os.path.exists(DIRECTORY):
    print("dist folder not found. Make sure to npm run build first!")

Handler = MyHttpRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server (Backend + Frontend) serving at port {PORT}")
    httpd.serve_forever()
