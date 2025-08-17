import requests
import subprocess
import sys
import time
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Optional, Dict, Any
from google import genai
#from pydub import AudioSegment  # NEW: for conversion
import ffmpeg

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

API_KEY = "c08f1e617e834d1ab1b70c2346c18bd4"  # Replace with your AssemblyAI API key
HEADERS = {'authorization': API_KEY}


# def convert_webm_to_mp3(webm_path: str) -> str:
#     """Convert a .webm file to .mp3 and return the new path."""
#     mp3_path = webm_path.replace(".webm", ".mp3")
#     print(f"Converting {webm_path} to {mp3_path}...")
#     audio = AudioSegment.from_file(webm_path, format="webm")
#     audio.export(mp3_path, format="mp3")
#     print("Conversion completed")
#     return mp3_path


def upload_audio(file_path: str) -> str:
    print(f"Uploading audio from {file_path}...")
    with open(file_path, 'rb') as f:
        response = requests.post(
            'https://api.assemblyai.com/v2/upload',
            headers=HEADERS,
            files={'file': f}
        )
    response.raise_for_status()
    upload_url = response.json().get('upload_url')
    if not upload_url:
        raise ValueError("Failed to get upload_url from AssemblyAI response")
    print(f"Audio uploaded, URL: {upload_url}")
    return upload_url


def start_transcription(audio_url: str) -> str:
    print("Starting transcription with diarization...")
    endpoint = 'https://api.assemblyai.com/v2/transcript'
    json_data = {'audio_url': audio_url, 'speaker_labels': True}
    response = requests.post(endpoint, json=json_data, headers=HEADERS)
    response.raise_for_status()
    transcript_id = response.json().get('id')
    if not transcript_id:
        raise ValueError("Failed to get transcript_id from AssemblyAI response")
    print(f"Transcription started, ID: {transcript_id}")
    return transcript_id


def wait_for_completion(transcript_id: str) -> Dict[str, Any]:
    polling_url = f'https://api.assemblyai.com/v2/transcript/{transcript_id}'
    print("Waiting for transcription to complete...")
    while True:
        response = requests.get(polling_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'completed':
            print("Transcription completed")
            return data
        elif data['status'] == 'error':
            raise Exception(f"Transcription failed: {data['error']}")
        time.sleep(5)


def record(data: Dict[str, Any]) -> str:
    transcript = "\n--- Diarized Transcript ---\n"
    for utterance in data.get('utterances', []):
        speaker = utterance['speaker']
        text = utterance['text']
        transcript += f"Speaker {speaker}: {text}\n"
    print("Generated transcript:\n", transcript)
    return transcript

def webm_to_mp3(input_path: str, output_path: str):
    """
    Converts a .webm file to .mp3 using ffmpeg.
    """
    try:
        # ffmpeg command
        command = [
            "ffmpeg",
            "-i", input_path,   # input file
            "-vn",              # no video
            "-acodec", "libmp3lame",  # use MP3 encoder
            "-q:a", "2",        # audio quality (lower is better, 2 is near CD quality)
            output_path
        ]
        subprocess.run(command, check=True)
        print(f"✅ Conversion successful: {output_path}")
    except subprocess.CalledProcessError as e:
        print("❌ Error during conversion:", e)



def generate_medical_report(transcript_data: Dict[str, Any]) -> str:
    instruction =  "Copilot you are a senior doctor in the medical field. You are aware that when we interact with patients it is mandatory to record the conversation in a way that is accurate and format medical notes that follws the standards outlined for all medical professions. These standards must note down every essential detail about the patient ,process and structure its information so it meets the medical health record standards. This record must be accurate and have the correct medical term in medical standard libraries and should be in a away that includes a standard of patient's meta data. So using this conversation that occurred between you and the patient draft a good medical report. Don't add any new information that's not included in the conversation, and don't make your own assumptions, just place the vital information from the conversation into accurate note structure: Clinical Note: Patient Name: <> Date of Birth: <> Age: <> Sex: <> Medical Record #: <> Date of clinic visit: <> Primary care provider: <> Personal note: <> History of Present Illness: <> Allergies: <> Medications: <> Previous History: Past Medical History: <> Past Surgical History: <> Family History: <> Social History: <> Review of Systems: <> Physical Exam: General appearance: <> Blood Pressure: <> Heart Rate: <> Respiratory Rate: <> Oxygen Saturation: <> Assessment: <> Plan: <> Medical Decision Making: <>\n\n"
    prompt = instruction + record(transcript_data)
    print("Sending prompt to Gemini API...")

    client = genai.Client(api_key="AIzaSyCjPdFvvzgMVGWN57axtKr_GAPVYlBtuBI")
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    response_text = response.text if hasattr(response, 'text') else str(response)
    if not isinstance(response_text, str):
        raise ValueError("Failed to get valid text response from Gemini API")
    print("Medical report generated")
    return response_text


@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    try:
        patient_id: Optional[str] = request.form.get('patientId')
        audio_file = request.files.get('audio')

        if not patient_id or not audio_file:
            print("Error: Missing patientId or audio file")
            return jsonify({'error': 'Missing patientId or audio file'}), 400

        file_name: str = audio_file.filename or f"{int(time.time() * 1000)}.webm"
        if not file_name.endswith('.webm'):
            print(f"Error: Invalid file format for {file_name}, expected .webm")
            return jsonify({'error': 'Invalid file format, expected .webm'}), 400

        recordings_dir: str = os.path.join('patients', patient_id, 'recordings')
        os.makedirs(recordings_dir, exist_ok=True)
        print(f"Created directory: {recordings_dir}")

        # Save .webm
        webm_path: str = os.path.join(recordings_dir, file_name)
        audio_file.save(webm_path)
        print(f"Audio file saved to: {webm_path}")

        # Convert to mp3
        webm_to_mp3(webm_path, webm_path.replace('.webm', '.mp3'))
        mp3_path = webm_path.replace('.webm', '.mp3')
        # mp3_path: str = os.path.join(recordings_dir, map)
        print(mp3_path)

        # Upload mp3
        audio_url = upload_audio(mp3_path)
        transcript_id = start_transcription(audio_url)
        transcript_data = wait_for_completion(transcript_id)

        # Generate report
        medical_report = generate_medical_report(transcript_data)

        # Cleanup
        os.remove(webm_path)
        os.remove(mp3_path)
        print(f"Deleted temp files: {webm_path}, {mp3_path}")

        print("Returning medical report")
        return jsonify({'medical_report': medical_report})

    except Exception as e:
        print(f"Error in /api/transcribe: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=8000)
