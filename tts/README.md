# Gerador de áudio MP3 (en/es/pt)

Envia textos para o backend [VoiceStudio](https://github.com/debpalash/VoiceStudio) (`/v1/audio/speech`) e salva MP3 em `output/`.
Sem dependências além do Python 3.10+.

```bash
python tts/tts.py --lang pt "Olá, mundo"      # CLI (também aceita stdin)
python tts/tts.py --serve --port 8080         # API HTTP
curl localhost:8080/tts -d '{"items":[{"text":"Hello","lang":"en"},{"text":"Hola","lang":"es"}]}'
```

Variáveis: `VOICESTUDIO_URL` (padrão `http://localhost:3900`), `VOICESTUDIO_TOKEN`, `TTS_OUT_DIR`, `VOICE_EN`/`VOICE_ES`/`VOICE_PT` (ID de perfil de voz).
Os MP3 ficam disponíveis em `GET /files/<nome>.mp3`.
