import uuid
from typing import Dict, Union

from fastapi import FastAPI, WebSocket
from pyaudio import paInt16

import config
from recording_session import RecordingSession
from websocket_handler import WebSocketHandler

app: FastAPI = FastAPI()

recording_sessions: Dict[str, RecordingSession] = {}

AUDIO_FORMAT_MAP = {"paInt16": paInt16}


@app.get("/")
def home() -> Dict[str, str]:
    return {"Prototype": "Transcriber"}


@app.post("/record/start")
async def start_recording() -> Dict[str, str]:
    session_id: str = str(uuid.uuid4())
    filename: str = f"recording_{session_id}.wav"

    session: RecordingSession = RecordingSession(
        session_id,
        AUDIO_FORMAT_MAP[config.FORMAT],
        config.CHANNELS,
        config.RATE,
        config.CHUNK,
        filename,
    )
    recording_sessions[session_id] = session
    session.start()

    return {"session_id": session_id, "status": "recording_started"}


@app.post("/record/stop/{session_id}")
async def stop_recording(session_id: str) -> Dict[str, Union[str, Dict[str, str]]]:
    if session_id not in recording_sessions:
        return {"error": "Session not found"}

    session: RecordingSession = recording_sessions[session_id]
    session.stop()
    filename: str = session.filename

    # Explicitly handle transcription
    try:
        await session.transcribe()
        transcription_result = session.transcription
    except Exception as e:
        transcription_result = f"Transcription error: {e}"

    del recording_sessions[session_id]

    return {
        "session_id": session_id,
        "status": "recording_stopped",
        "file": filename,
        "transcription": transcription_result,
    }


@app.get("/record/status/{session_id}")
async def recording_status(session_id: str) -> Dict[str, Union[str, bool, int]]:
    if session_id not in recording_sessions:
        return {"error": "Session not found"}

    session: RecordingSession = recording_sessions[session_id]
    return {
        "session_id": session_id,
        "recording": session.recording,
        "frames_recorded": len(session.frames),
    }


@app.websocket("/record/ws")
async def recording_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    handler = WebSocketHandler(websocket)

    await websocket.send_text("Connected! Commands: start, stop, status, help")

    try:
        while True:
            message: str = await websocket.receive_text()
            await handler.handle_message(message)
            if message.strip().lower() == "quit":
                break

    except Exception as e:
        print(f"WebSocket error: {e}")
        if handler.session:
            handler.session.stop()
        await websocket.close()
