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

## Deploy no Vercel

`api/tts.py` é uma função serverless: `POST /api/tts {"text":"...","lang":"pt"}` devolve o MP3 direto (nada é gravado em disco).

Variáveis de ambiente no Vercel:
- `VOICESTUDIO_URL` — URL **pública** do backend VoiceStudio (não funciona com `localhost`)
- `VOICESTUDIO_TOKEN` — credencial do backend, se protegido
- `TTS_API_KEY` — recomendado: exige `Authorization: Bearer <chave>` neste endpoint
- `VOICE_EN`/`VOICE_ES`/`VOICE_PT` — opcional

```bash
curl -X POST https://SEU-APP.vercel.app/api/tts -H "Authorization: Bearer $TTS_API_KEY" \
  -d '{"text":"Hello","lang":"en"}' -o hello.mp3
```

Abra a raiz do site (`public/index.html`) para usar pelo navegador: escolha o idioma, cole o texto e baixe o MP3.

Limites: resposta de até ~4,5 MB por requisição e `maxDuration` de 60 s (ajuste em `vercel.json` conforme o plano).
