import os

from dotenv import load_dotenv
from openai import APIError, OpenAI

load_dotenv()


client: OpenAI = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


async def transcribe_audio(filename: str, session_id: str) -> str:
    """Transcribe audio file and save transcription."""
    print(f"Transcribing audio in {filename}")

    try:
        with open(filename, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe", file=audio_file, response_format="text"
            )

        transcribed_text: str = transcription
        transcription_file: str = f"transcription_{session_id}.txt"

        with open(transcription_file, "w", encoding="utf-8") as f:
            f.write(transcribed_text)

        print(f"Transcription saved to: {transcription_file}")
        print("\nTranscribed Text:")
        print(transcribed_text)

        return transcribed_text

    except APIError as e:
        print(f"OpenAI API error: {e}")
        raise  # Re-raise the original APIError
    except FileNotFoundError as e:
        print(f"Audio file not found: {e}")
        raise
    except Exception as e:
        print(f"Unexpected transcription error: {e}")
        raise
