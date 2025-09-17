# Transcriber

A real-time audio recording and transcription API built with FastAPI and OpenAI Whisper. Transcriber allows you to start/stop audio recording sessions via REST endpoints and automatically transcribes the recorded audio using OpenAI's speech-to-text API.

## Features

- 🎤 **Real-time Audio Recording**: Multi-threaded audio recording using PyAudio
- 🔄 **Session Management**: Start/stop recording sessions with unique session IDs
- 📝 **Automatic Transcription**: Integrates with OpenAI's Whisper model for speech-to-text
- 🌐 **REST API**: Simple HTTP endpoints for easy integration
- � **WebSocket Support**: Real-time interactive recording control
- �📊 **Session Status**: Monitor active recording sessions and progress
- 💾 **File Output**: Saves both audio files (.wav) and transcription text files

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check endpoint |
| `POST` | `/record/start` | Start a new recording session |
| `POST` | `/record/stop/{session_id}` | Stop recording and transcribe audio |
| `GET` | `/record/status/{session_id}` | Get recording session status |
| `WebSocket` | `/record/ws` | Real-time recording control via WebSocket |

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Audio input device (microphone)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/imran-salim/transcriber.git
   cd transcriber
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

### Running the Application

1. **Start the server**
   ```bash
   fastapi dev main.py
   ```

2. **The API will be available at**
   - Local: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs

### Usage Examples

#### Using cURL

**Start Recording:**
```bash
curl -X POST http://localhost:8000/record/start
# Returns: {"session_id": "uuid-here", "status": "recording_started"}
```

**Stop Recording:**
```bash
curl -X POST http://localhost:8000/record/stop/{session_id}
# Returns: {"session_id": "uuid", "status": "recording_stopped", "file": "recording_uuid.wav"}
```

**Check Status:**
```bash
curl http://localhost:8000/record/status/{session_id}
# Returns: {"session_id": "uuid", "recording": true, "frames_recorded": 1234}
```

#### Using Python requests

```python
import requests

# Start recording
response = requests.post('http://localhost:8000/record/start')
session_data = response.json()
session_id = session_data['session_id']

# Record for some time...
input('Press Enter to stop recording...')

# Stop recording
response = requests.post(f'http://localhost:8000/record/stop/{session_id}')
result = response.json()
print(f'Recording saved to: {result['file']}')
```

### WebSocket Interface

The API also supports WebSocket connections for real-time interaction:

#### WebSocket Commands
- `start` - Begin recording
- `stop` - End recording, save file, and transcribe automatically
- `status` - Check recording status with duration
- `help` - Show available commands
- `quit` - Close connection

#### Testing WebSocket
```bash
# Install websocat for testing
brew install websocat  # macOS

# Connect to WebSocket
websocat ws://localhost:8000/record/ws

# Use commands interactively:
start    # 🎤 Recording started: session-id
status   # 📊 Recording active | Session: session-id | Frames: 1234 | Duration: ~5.2s
stop     # 🛑 Recording stopped, 🔄 Starting transcription..., ✅ Transcription complete
```

#### WebSocket Python Client
```python
import asyncio
import websockets

async def test_recording():
    uri = 'ws://localhost:8000/record/ws'
    
    async with websockets.connect(uri) as websocket:
        # Start recording
        await websocket.send('start')
        response = await websocket.recv()
        print(f'Start: {response}')
        
        # Wait and check status
        await asyncio.sleep(3)
        await websocket.send('status')
        response = await websocket.recv()
        print(f'Status: {response}')
        
        # Stop and transcribe
        await websocket.send('stop')
        response = await websocket.recv()
        print(f'Stop: {response}')
        
        # Get transcription result
        response = await websocket.recv()
        print(f'Transcription: {response}')

asyncio.run(test_recording())
```

## Technical Details

### Audio Configuration
- **Format**: 16-bit PCM
- **Channels**: Mono (1 channel)
- **Sample Rate**: 44,100 Hz
- **Chunk Size**: 1024 frames

### File Outputs
- **Audio Files**: `recording_{session_id}.wav`
- **Transcription Files**: `transcription_{session_id}`

### Architecture

The application uses:
- **FastAPI** for the REST API framework
- **PyAudio** for real-time audio recording
- **Threading** for non-blocking recording sessions
- **OpenAI API** for speech transcription
- **Wave** module for audio file handling

### Key Components

1. **RecordingSession Class**: Manages individual recording sessions with threading
2. **Session Management**: Global dictionary tracking active recording sessions
3. **Error Handling**: Comprehensive exception handling for audio and API errors

## Development

### Project Structure
```
transcriber/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (not in repo)
├── .gitignore          # Git ignore rules
├── LICENSE             # MIT License file
├── README.md           # This file
└── __pycache__/        # Python cache files
```

### Dependencies

Key packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pyaudio` - Audio I/O
- `openai` - OpenAI API client
- `python-dotenv` - Environment variable management

## Troubleshooting

### Common Issues

1. **PyAudio Installation Issues**
   ```bash
   # macOS
   brew install portaudio
   pip install pyaudio
   
   # Ubuntu/Debian
   sudo apt-get install portaudio19-dev python3-pyaudio
   pip install pyaudio
   ```

2. **Permission Denied for Microphone**
   - Ensure microphone permissions are granted to your terminal/IDE
   - On macOS: System Preferences → Security & Privacy → Microphone

3. **OpenAI API Errors**
   - Verify your API key is valid and has sufficient credits
   - Check the model name is correct: `gpt-4o-mini-transcribe`

### Error Codes

- `404`: Session not found
- `500`: Internal server error (check logs for audio/API issues)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add some feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Roadmap

- [x] ✅ WebSocket support for real-time transcription
- [ ] Multiple audio format support
- [ ] Batch processing capabilities
- [ ] Authentication and rate limiting
- [ ] Docker containerization
- [ ] Frontend web interface
- [ ] Background processing for large files
- [ ] Audio quality enhancement options

---

**Built with ❤️ for seamless audio transcription workflows**