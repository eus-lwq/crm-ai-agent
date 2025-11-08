import os
import requests

def transcribe_audio_groq(local_path: str) -> str:
    """
    Uses Groq's Whisper API to transcribe audio.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY environment variable")

    url = "https://api.groq.com/openai/v1/audio/transcriptions"

    with open(local_path, "rb") as audio_file:
        files = {"file": (local_path, audio_file, "audio/mpeg")}
        data = {"model": "whisper-large-v3"}
        headers = {"Authorization": f"Bearer {api_key}"}

        print("Sending file to Groq Whisper for transcription...")
        response = requests.post(url, headers=headers, data=data, files=files)
        response.raise_for_status()

        result = response.json()
        transcript = result.get("text", "")
        
        return transcript
