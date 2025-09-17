# Transcriber

Minimal real-time audio recording + transcription API using FastAPI, PyAudio and OpenAI.

## Features
- Start / stop microphone capture
- WAV file output + text transcription
- REST + WebSocket control
- Simple session status

## Install
```bash
git clone https://github.com/imran-salim/transcriber.git
cd transcriber
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
echo 'OPENAI_API_KEY=your_key' > .env
```

## Run
```bash
fastapi dev main.py
# Docs: http://localhost:8000/docs
```

## REST API
```text
POST /record/start          -> { session_id, status }
POST /record/stop/{id}      -> { session_id, status, file }
GET  /record/status/{id}    -> { session_id, recording, frames_recorded }
WS   /record/ws             -> commands: start | stop | status | help | quit
```

## Quick Usage
```bash
curl -X POST http://localhost:8000/record/start
curl http://localhost:8000/record/status/{session_id}
curl -X POST http://localhost:8000/record/stop/{session_id}
```

## WebSocket
```bash
websocat ws://localhost:8000/record/ws
> start
> status
> stop
```

## Notes
- Audio: 16-bit PCM mono 44.1kHz
- Output: recording_<id>.wav + transcription_<id>
- Model: gpt-4o-mini-transcribe (configure in code if needed)

## License
MIT

---
Built for quick experimentation.