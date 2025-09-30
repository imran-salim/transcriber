import uuid
from typing import Optional

from fastapi import WebSocket
from pyaudio import paInt16

from recording_session import RecordingSession


class WebSocketHandler:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.session: Optional[RecordingSession] = None

    async def handle_message(self, message: str):
        message = message.strip().lower()
        print(f"Received WebSocket message: {message}")

        if message == "start" and self.session is None:
            await self.start_recording()
        elif message == "start" and self.session is not None:
            await self.websocket.send_text("⚠️ Recording already in progress")
        elif message == "stop" and self.session is not None:
            await self.stop_recording()
        elif message == "stop" and self.session is None:
            await self.websocket.send_text("⚠️ No active recording to stop")
        elif message == "status":
            await self.send_status()
        elif message == "help":
            await self.send_help()
        elif message == "quit":
            await self.websocket.send_text("👋 Goodbye!")
        else:
            await self.websocket.send_text(
                f"❓ Unknown command: '{message}'. Type 'help' for available commands."
            )

    async def start_recording(self):
        try:
            session_id: str = str(uuid.uuid4())
            filename: str = f"recording_{session_id}.wav"
            self.session = RecordingSession(
                session_id, paInt16, 1, 44100, 1024, filename
            )
            self.session.start()
            await self.websocket.send_text(f"🎤 Recording started: {session_id}")
            print(f"WebSocket: Started recording {session_id}")

        except Exception as e:
            await self.websocket.send_text(f"❌ Error starting recording: {e}")
            print(f"WebSocket start error: {e}")

    async def stop_recording(self):
        try:
            self.session.stop()
            await self.websocket.send_text(
                f"🛑 Recording stopped, saved to {self.session.filename}"
            )
            await self.websocket.send_text("🔄 Starting transcription...")

            try:
                await self.session.transcribe()
                await self.websocket.send_text(
                    f"✅ Transcription complete: transcription_{self.session.session_id}.txt"
                )
                await self.websocket.send_text(f"📝 Text: {self.session.transcription}")

            except Exception as e:
                await self.websocket.send_text(f"❌ Transcription error: {e}")

            self.session = None
        except Exception as e:
            await self.websocket.send_text(f"❌ Error stopping recording: {e}")
            print(f"WebSocket stop error: {e}")

    async def send_status(self):
        if self.session:
            duration: float = len(self.session.frames) * 1024 / 44100
            await self.websocket.send_text(
                f"📊 Recording active | Session: {self.session.session_id} | Frames: {len(self.session.frames)} | Duration: ~{duration:.1f}s"
            )
        else:
            await self.websocket.send_text("💤 No active recording")

    async def send_help(self):
        await self.websocket.send_text('📋 Available commands:')
        await self.websocket.send_text('• start  - Begin recording')
        await self.websocket.send_text('• stop   - End recording and save')
        await self.websocket.send_text('• status - Check recording status')
        await self.websocket.send_text('• help   - Show this message')
        await self.websocket.send_text('• quit   - Close connection')
