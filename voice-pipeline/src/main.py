import json
from google.cloud import storage
from transcriber import transcribe_audio_groq
from extractor import extract_crm_fields
from bigquery_utils import insert_into_bigquery

def on_file_upload(event, context):
    bucket_name = event['bucket']
    file_name = event['name']

    if not file_name.endswith(('.mp3', '.wav', '.m4a')):
        print(f"Skipping non-audio file: {file_name}")
        return

    print(f"New audio file uploaded: {file_name}")

    # Download the file locally
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    local_path = f"/tmp/{file_name.split('/')[-1]}"
    blob.download_to_filename(local_path)
    print(f"Downloaded to {local_path}")

    # Step 1: Transcribe using Groq Whisper
    transcript = transcribe_audio_groq(local_path)
    print(f"Transcript: {transcript[:200]}...")

    # Step 2: Extract CRM data using LangChain + Groq
    structured_data = extract_crm_fields(transcript)

    # Step 3: Insert structured data into BigQuery
    insert_into_bigquery(structured_data)

    print(f"Data inserted into BigQuery for file: {file_name}")
