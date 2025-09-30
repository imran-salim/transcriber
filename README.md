# Transcriber

Real-time audio recording and transcription using FastAPI, PyAudio, and OpenAI.

## Setup
```bash
git clone https://github.com/imran-salim/transcriber.git
cd transcriber
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo 'OPENAI_API_KEY=your_key' > .env
```

## Run
```bash
fastapi dev main.py
# http://localhost:8000/docs
```

## API
```
POST /record/start          # Start recording
POST /record/stop/{id}      # Stop & transcribe  
GET  /record/status/{id}    # Check status
WS   /record/ws             # WebSocket interface
```

## Usage
```bash
# REST
curl -X POST http://localhost:8000/record/start
curl -X POST http://localhost:8000/record/stop/{session_id}

# WebSocket
websocat ws://localhost:8000/record/ws
> start
> stop
> quit
```

## Output
- Audio: `recording_{id}.wav`
- Text: `transcription_{id}.txt`

## License
MIT