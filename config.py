from pyaudio import paInt16

# Audio settings
FORMAT = "paInt16"
CHANNELS = 1
RATE = 44100
CHUNK = 1024
AUDIO_FORMAT_MAP = {'paInt16': paInt16}

# Transcription settings
MODEL = "gpt-4o-mini-transcribe"
