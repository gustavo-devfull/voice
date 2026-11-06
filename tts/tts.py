"""Gera MP3 (en/es/pt) a partir de textos usando o backend VoiceStudio.

Uso CLI:   python tts.py --lang pt "Olá, mundo"        |  echo "Hola" | python tts.py --lang es
Uso HTTP:  python tts.py --serve   (POST /tts {"text": "...", "lang": "en"})
Somente biblioteca padrão do Python.
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BACKEND = os.environ.get("VOICESTUDIO_URL", "http://localhost:3900").rstrip("/")
TOKEN = os.environ.get("VOICESTUDIO_TOKEN")  # opcional
OUT_DIR = Path(os.environ.get("TTS_OUT_DIR", "output"))
LANGS = {"en": "English", "es": "Español", "pt": "Português"}
# Voz por idioma (ID de perfil do VoiceStudio); padrão: voz default do motor.
VOICES = {l: os.environ.get(f"VOICE_{l.upper()}", "default") for l in LANGS}
MAX_CHARS = 5000


def synthesize_bytes(text: str, lang: str, voice: str | None = None) -> bytes:
    lang = lang.lower()[:2]
    if lang not in LANGS:
        raise ValueError(f"idioma inválido '{lang}'; use: {', '.join(LANGS)}")
    text = text.strip()
    if not text:
        raise ValueError("texto vazio")
    if len(text) > MAX_CHARS:
        raise ValueError(f"texto muito longo (máx. {MAX_CHARS} caracteres)")
    body = json.dumps({"model": "tts-1", "voice": voice or VOICES[lang], "input": text,
                       "language": lang, "response_format": "mp3"}).encode()
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(f"{BACKEND}/v1/audio/speech", body, headers)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"backend HTTP {e.code}: {e.read()[:300].decode(errors='replace')}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"backend VoiceStudio indisponível em {BACKEND}: {e.reason}")
    # Erro pode vir como JSON; MP3 válido começa com 'ID3' ou sync de frame 0xFF 0xEx.
    if not (data[:3] == b"ID3" or (len(data) > 2 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0)):
        raise RuntimeError(f"resposta não é MP3: {data[:200]!r}")
    return data


def synthesize(text: str, lang: str, voice: str | None = None) -> Path:
    data = synthesize_bytes(text, lang, voice)
    lang = lang.lower()[:2]
    slug = re.sub(r"\W+", "-", text[:40], flags=re.U).strip("-").lower() or "audio"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-{lang}-{slug}.mp3"
    path.write_bytes(data)
    return path


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"ok": True, "langs": list(LANGS)})
        if self.path.startswith("/files/"):
            f = OUT_DIR / Path(self.path[7:]).name
            if f.suffix == ".mp3" and f.is_file():
                b = f.read_bytes()
                self.send_response(200); self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(b))); self.end_headers()
                return self.wfile.write(b)
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/tts":
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(n) or b"{}")
            # aceita um texto ou uma lista em "items": [{"text","lang"}]
            items = d.get("items") or [d]
            out = []
            for it in items:
                p = synthesize(it.get("text", ""), it.get("lang", ""), it.get("voice"))
                out.append({"lang": it["lang"], "file": str(p), "url": f"/files/{p.name}"})
            self._json(200, {"results": out})
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            self._json(400, {"error": str(e)})
        except RuntimeError as e:
            self._json(502, {"error": str(e)})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?", help="texto (ou via stdin)")
    ap.add_argument("--lang", choices=LANGS, help="en | es | pt")
    ap.add_argument("--voice"); ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8080)
    a = ap.parse_args()
    if a.serve:
        print(f"Servidor em http://0.0.0.0:{a.port}  (backend: {BACKEND})")
        ThreadingHTTPServer(("0.0.0.0", a.port), Handler).serve_forever()
    if not a.lang:
        ap.error("--lang é obrigatório")
    text = a.text if a.text is not None else sys.stdin.read()
    try:
        print(synthesize(text, a.lang, a.voice))
    except (ValueError, RuntimeError) as e:
        sys.exit(f"erro: {e}")


if __name__ == "__main__":
    main()
