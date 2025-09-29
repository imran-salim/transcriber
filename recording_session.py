import wave
from pyaudio import PyAudio, paInt16
from threading import Thread


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