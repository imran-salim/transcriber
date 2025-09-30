import wave
from threading import Thread

from pyaudio import PyAudio

from transcriber import transcribe_audio


class RecordingSession:
    def __init__(
        self,
        session_id: str,
        format: int,
        channels: int,
        rate: int,
        chunk: int,
        filename: str,
    ) -> None:
        self.session_id: str = session_id
        self.format: int = format
        self.channels: int = channels
        self.rate: int = rate
        self.chunk: int = chunk
        self.audio: PyAudio = PyAudio()
        self.stream = self.audio.open(
            format=format,
            channels=channels,
            rate=rate,
            input=True,
            frames_per_buffer=chunk,
        )
        self.frames: list[bytes] = []
        self.recording: bool = True
        self.filename: str = filename
        self.thread: Thread = Thread(target=self._record)
        self.transcription: str = ""

    def _record(self) -> None:
        while self.recording:
            try:
                data: bytes = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"Recording error: {e}")
                break

    def start(self) -> None:
        self.thread.start()
        print(f"Started recording session {self.session_id}")

    def stop(self) -> None:
        self.recording = False
        self.thread.join()

        wf: wave.Wave_write = wave.open(self.filename, "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b"".join(self.frames))
        wf.close()

        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

        print(f"Stopped recording session {self.session_id}, saved to {self.filename}")

    async def transcribe(self) -> None:
        try:
            self.transcription = await transcribe_audio(self.filename, self.session_id)
        except Exception as e:
            print(f"Transcription error: {e}")
            self.transcription = f"Error: {e}"
