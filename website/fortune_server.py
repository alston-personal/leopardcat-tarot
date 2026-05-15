import http.server
import socketserver
import json
import urllib.request
import urllib.error
import os
import ssl
import traceback
import sys

PORT = 8088
DIRECTORY = "dist"

def log(msg):
    print(msg, flush=True)

def update_stats(divination=False):
    try:
        if not os.path.exists('stats.json'):
            with open('stats.json', 'w') as f: 
                json.dump({"total_visitors": 2026, "total_divinations": 888}, f)
        
        with open('stats.json', 'r+') as sf:
            sdata = json.load(sf)
            if divination:
                sdata['total_divinations'] = sdata.get('total_divinations', 0) + 1
            else:
                sdata['total_visitors'] = sdata.get('total_visitors', 0) + 1
            sf.seek(0)
            json.dump(sdata, sf)
            sf.truncate()
            return sdata
    except Exception as e:
        log(f"Error updating stats: {e}")
        return {"total_visitors": 2026, "total_divinations": 888, "error": str(e)}

def load_env_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        env_path = "/home/ubuntu/agentmanager/.env"
        if os.path.exists(env_path):
            try:
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            key = line.strip().split("=", 1)[1]
                            break
            except Exception as e:
                log(f"Error reading .env: {e}")
    return key

API_KEY = load_env_key()
log(f"API Key loaded (first 5 chars): {API_KEY[:5] if API_KEY else 'NONE'}")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        url_parts = self.path.split('?', 1)
        path = url_parts[0]
        if path == '/api/stats':
            sdata = update_stats(divination=False)
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
                req_data = json.loads(post_data.decode('utf-8'))
                question = req_data.get('question', '')
                card_title = req_data.get('cardTitle', 'TBD')
                card_meaning = req_data.get('cardMeaning', '')
                lang = req_data.get('lang', 'zh')
                history = req_data.get('history', [])

                log(f"Fortune Request: Q='{question}', Card='{card_title}', Lang='{lang}', History_len={len(history)}")

                contents = []
                for h in history:
                    role = "user" if h['role'] == 'user' else "model"
                    contents.append({"role": role, "parts": [{"text": h['content']}]})
                
                # System prompt + latest question
                system_lang = "Traditional Chinese (Taiwan)" if lang == 'zh' else "English"
                system_prompt = f"You are the 'Hill Spirit Master' of a Leopard Cat Tarot deck, a wise guardian of the shallow mountains. Connect the leopard cat's survival journey to the seeker's life. "
                
                if lang == 'zh':
                    system_prompt += (
                        "你的口吻神祕、優雅且富有禪意。在解牌時，必須將石虎的現實生存困境（如棲地破碎化、路殺、犬隻攻擊、非法獵捕）與牌義結合，"
                        "引導求問者在解決自身生命難題的同時，也能感同身受淺山靈魂的艱辛。絕對禁止使用簡體中文，必須使用台灣繁體中文，且禁用中國大陸用語。"
                        "\n\n**語言規範**：請優先以求問者的提問語言回覆，展現你通曉萬物靈魂的智慧。若無法判斷語言，則預設以「台灣繁體中文」回答。"
                    )
                else:
                    system_prompt += (
                        "Your tone is mystical, elegant, and Zen-like. When reading, weave specific Leopard Cat conservation challenges "
                        "(e.g., habitat fragmentation, roadkill, stray dog attacks, illegal trapping) into the interpretation. "
                        "\n\n**LANGUAGE POLICY**: You MUST respond in the seeker's language to ensure a deep soul connection. If the seeker's language is unclear or if they are just using symbols, default to English. "
                        "\n\n**CRITICAL**: At the end of EVERY response, you MUST provide a short, profound 'Golden Quote' (max 20 words) that summarizes the core blessing or insight. "
                        "Wrap it EXACTLY like this: <div class='hidden-quote' style='display:none'>[Your Quote Here]</div>"
                    )

                system_prompt += f"\n\nThe seeker drew: {card_title} ({card_meaning})."
                
                if not contents:
                    contents.append({"role": "user", "parts": [{"text": f"{system_prompt}\n\nQuestion: {question}"}]})
                else:
                    contents.append({"role": "user", "parts": [{"text": question}]})

                payload = {"contents": contents}
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
                
                req = urllib.request.Request(gemini_url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                
                log(f"Calling Gemini API...")
                with urllib.request.urlopen(req, context=ctx) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    reading = res_data['candidates'][0]['content']['parts'][0]['text']
                    log(f"Gemini Response Success (len={len(reading)})")
                update_stats(divination=True)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"reading": reading}).encode('utf-8'))
                
            except Exception as e:
                log(f"!!! FORTUNE ERROR: {e}")
                traceback.print_exc(file=sys.stdout)
                sys.stdout.flush()
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e), "reading": "（大師閉目沉思中，請稍後再試...）"}).encode('utf-8'))
        else:
            self.send_error(404)

socketserver.TCPServer.allow_reuse_address = True
# Use ThreadingTCPServer to handle multiple concurrent asset requests (essential for mobile gallery performance)
with socketserver.ThreadingTCPServer(("", PORT), MyHttpRequestHandler) as httpd:
    log(f"LCS Server running on {PORT} (Multi-threaded)")
    httpd.serve_forever()
