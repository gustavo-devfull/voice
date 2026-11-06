"""Função serverless do Vercel: POST /api/tts {"text": "...", "lang": "en|es|pt"} -> audio/mpeg."""
import hmac, importlib.util, json, os
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_spec = importlib.util.spec_from_file_location("tts_core", Path(__file__).resolve().parent.parent / "tts" / "tts.py")
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)

API_KEY = os.environ.get("TTS_API_KEY")  # se definida, exige "Authorization: Bearer <chave>"
MAX_BODY = 20_000


class handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._json(200, {"ok": True, "langs": list(core.LANGS), "usage": 'POST {"text","lang"}'})

    def do_POST(self):
        if API_KEY:
            got = self.headers.get("Authorization", "")
            if not hmac.compare_digest(got, f"Bearer {API_KEY}"):
                return self._json(401, {"error": "não autorizado"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > MAX_BODY:
                return self._json(413, {"error": "corpo muito grande"})
            d = json.loads(self.rfile.read(n) or b"{}")
            audio = core.synthesize_bytes(d.get("text", ""), d.get("lang", ""), d.get("voice"))
        except (ValueError, json.JSONDecodeError) as e:
            return self._json(400, {"error": str(e)})
        except RuntimeError as e:
            return self._json(502, {"error": str(e)})
        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Content-Disposition", f'attachment; filename="audio-{d["lang"][:2].lower()}.mp3"')
        self.send_header("Content-Length", str(len(audio)))
        self.end_headers()
        self.wfile.write(audio)
