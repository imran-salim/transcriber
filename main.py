from pyaudio import PyAudio, paInt16
import wave
import os
from dotenv import load_dotenv 
from threading import Thread
import uuid
from openai import OpenAI, APIError

from typing import Union, Dict, Optional

from fastapi import FastAPI, WebSocket

load_dotenv()

app: FastAPI = FastAPI()

client: OpenAI = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

recording_sessions: Dict[str, 'RecordingSession'] = {}

class RecordingSession:
    def __init__(self, session_id: str, format: int, channels: int, rate: int, chunk: int, filename: str) -> None:
        self.session_id: str = session_id
        self.audio: PyAudio = PyAudio()
        self.stream = self.audio.open(format=format,
                                      channels=channels,
                                      rate=rate,
                                      input=True,
                                      frames_per_buffer=chunk)
        self.frames: list[bytes] = []
        self.recording: bool = True
        self.filename: str = filename
        self.thread: Thread = Thread(target=self._record)

    def _record(self) -> None:
        while self.recording:
            try:
                data: bytes = self.stream.read(1024, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f'Recording error: {e}')
                break

    def start(self) -> None:
        self.thread.start()
        print(f'Started recording session {self.session_id}')

    def stop(self) -> None:
        self.recording = False
        self.thread.join()

        wf: wave.Wave_write = wave.open(self.filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

        print(f'Stopped recording session {self.session_id}, saved to {self.filename}')


@app.get('/')
def home() -> Dict[str, str]:
    return { 'Prototype': 'Transcriber' }


@app.post('/record/start')
async def start_recording() -> Dict[str, str]:
    session_id: str = str(uuid.uuid4())
    filename: str = f'recording_{session_id}.wav'

    session: RecordingSession = RecordingSession(session_id, paInt16, 1, 44100, 1024, filename)
    recording_sessions[session_id] = session
    session.start()

    return { 'session_id': session_id, 'status': 'recording_started' }


async def transcribe_audio(filename: str, session_id: str) -> str:
    """Transcribe audio file and save transcription."""
    print(f'Transcribing audio in {filename}')
    
    try:
        with open(filename, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model='gpt-4o-mini-transcribe',
                file=audio_file,
                response_format='text'
            )

        transcribed_text: str = transcription
        transcription_file: str = f'transcription_{session_id}.txt'
        
        with open(transcription_file, 'w', encoding='utf-8') as f:
            f.write(transcribed_text)

        print(f'Transcription saved to: {transcription_file}')
        print('\nTranscribed Text:')
        print(transcribed_text)
        
        return transcribed_text
        
    except APIError as e:
        error_msg: str = f'An OpenAI API error occurred: {e}'
        print(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg: str = f'An unexpected error occurred: {e}'
        print(error_msg)
        raise Exception(error_msg)


@app.post('/record/stop/{session_id}')
async def stop_recording(session_id: str) -> Dict[str, Union[str, Dict[str, str]]]:
    if session_id not in recording_sessions:
        return {'error': 'Session not found'}
    
    session: RecordingSession = recording_sessions[session_id]
    session.stop()
    filename: str = session.filename
    del recording_sessions[session_id]

    try:
        transcribed_text: str = await transcribe_audio(filename, session_id)
        return {
            'session_id': session_id, 
            'status': 'recording_stopped', 
            'file': filename,
            'transcription': transcribed_text
        }
    except Exception as e:
        return {
            'session_id': session_id,
            'status': 'recording_stopped',
            'file': filename,
            'transcription_error': str(e)
        }


@app.get('/record/status/{session_id}')
async def recording_status(session_id: str) -> Dict[str, Union[str, bool, int]]:
    if session_id not in recording_sessions:
        return {'error': 'Session not found'}
    
    session: RecordingSession = recording_sessions[session_id]
    return {'session_id': session_id, 'recording': session.recording, 'frames_recorded': len(session.frames)}


@app.websocket('/record/ws')
async def recording_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    session: Optional[RecordingSession] = None
    
    await websocket.send_text('Connected! Commands: start, stop, status, help')
    
    try:
        while True:
            message: str = await websocket.receive_text()
            message = message.strip().lower()
            print(f'Received WebSocket message: {message}')
            
            if message == 'start' and session is None:
                try:
                    session_id: str = str(uuid.uuid4())
                    filename: str = f'recording_{session_id}.wav'
                    session = RecordingSession(session_id, paInt16, 1, 44100, 1024, filename)
                    session.start()
                    await websocket.send_text(f'🎤 Recording started: {session_id}')
                    print(f'WebSocket: Started recording {session_id}')

                except Exception as e:
                    await websocket.send_text(f'❌ Error starting recording: {e}')
                    print(f'WebSocket start error: {e}')
  
            elif message == 'start' and session is not None:
                await websocket.send_text('⚠️ Recording already in progress')
                
            elif message == 'stop' and session is not None:
                try:
                    session.stop()
                    await websocket.send_text(f'🛑 Recording stopped, saved to {session.filename}')
                    await websocket.send_text('🔄 Starting transcription...')
                    
                    try:
                        transcribed_text: str = await transcribe_audio(session.filename, session.session_id)
                        await websocket.send_text(f'✅ Transcription complete: transcription_{session.session_id}.txt')
                        await websocket.send_text(f'📝 Text: {transcribed_text}')
                        
                    except Exception as e:
                        await websocket.send_text(f'❌ Transcription error: {e}')
        
                    session = None
                except Exception as e:
                    await websocket.send_text(f'❌ Error stopping recording: {e}')
                    print(f'WebSocket stop error: {e}')
                    
            elif message == 'stop' and session is None:
                await websocket.send_text('⚠️ No active recording to stop')
                
            elif message == 'status':
                if session:
                    duration: float = len(session.frames) * 1024 / 44100
                    await websocket.send_text(f'📊 Recording active | Session: {session.session_id} | Frames: {len(session.frames)} | Duration: ~{duration:.1f}s')
                else:
                    await websocket.send_text('💤 No active recording')
      
            elif message == 'help':
                help_text: str = """
                    📋 Available commands:
                    • start  - Begin recording
                    • stop   - End recording and save
                    • status - Check recording status
                    • help   - Show this message
                    • quit   - Close connection
                """
                await websocket.send_text(help_text)
                
            elif message == 'quit':
                await websocket.send_text('👋 Goodbye!')
                break
                
            else:
                await websocket.send_text(f'❓ Unknown command: \'{message}\'. Type \'help\' for available commands.')
                                 
    except Exception as e:
        print(f'WebSocket error: {e}')
        if session:
            session.stop()
        await websocket.close()
