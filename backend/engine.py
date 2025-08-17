import requests
import subprocess
import sys
import time
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Optional, Dict, Any
from google import genai
import re
import json
from datetime import datetime
#from pydub import AudioSegment  # NEW: for conversion

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

def clinical_note_to_json(file_content):
    """
    Parse a clinical note text file and return a structured JSON object.
    
    Args:
        file_content (str): The content of the clinical note text file.
    
    Returns:
        dict: A JSON-compatible dictionary containing the parsed clinical note data.
    """
    # Initialize the JSON structure
    clinical_data = {
        "patient": {},
        "visit": {},
        "medical_history": {},
        "examination": {},
        "assessment": {},
        "plan": {},
        "decision_making": {}
    }
    
    # Split content into lines for parsing
    lines = file_content.strip().split('\n')
    current_section = None
    
    # Helper function to clean text
    def clean_text(text):
        return text.strip().replace('\n', ' ')
    
    # Parse each line based on known headers
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Section headers
        if line.startswith('Clinical Note:'):
            current_section = 'clinical_note'
        elif line.startswith('Patient Name:'):
            clinical_data['patient']['name'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Date of Birth:'):
            dob = clean_text(line.split(':', 1)[1])
            clinical_data['patient']['date_of_birth'] = dob
            # Calculate age from DOB
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            clinical_data['patient']['age'] = f"{age} years"
        elif line.startswith('Age:'):
            # Age is already calculated from DOB, skip
            continue
        elif line.startswith('Sex:'):
            clinical_data['patient']['sex'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Medical Record #:'):
            clinical_data['patient']['medical_record_number'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Date of clinic visit:'):
            clinical_data['visit']['date'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Primary care provider:'):
            clinical_data['visit']['primary_care_provider'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Personal note:'):
            clinical_data['patient']['personal_note'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('History of Present Illness:'):
            current_section = 'history_of_present_illness'
            clinical_data['medical_history']['history_of_present_illness'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Allergies:'):
            clinical_data['medical_history']['allergies'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Medications:'):
            clinical_data['medical_history']['medications'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Previous History:'):
            current_section = 'previous_history'
            clinical_data['medical_history']['past_medical_history'] = []
            clinical_data['medical_history']['past_surgical_history'] = []
            clinical_data['medical_history']['family_history'] = []
            clinical_data['medical_history']['social_history'] = []
        elif line.startswith('Review of Systems:'):
            current_section = 'review_of_systems'
            clinical_data['examination']['review_of_systems'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Physical Exam:'):
            current_section = 'physical_exam'
            clinical_data['examination']['physical_exam'] = {}
        elif line.startswith('Vital Signs:'):
            current_section = 'vital_signs'
            clinical_data['examination']['vital_signs'] = {}
        elif line.startswith('Assessment:'):
            current_section = 'assessment'
            clinical_data['assessment']['diagnosis'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Plan:'):
            current_section = 'plan'
            clinical_data['plan']['treatment'] = clean_text(line.split(':', 1)[1])
        elif line.startswith('Medical Decision Making:'):
            current_section = 'decision_making'
            clinical_data['decision_making']['notes'] = clean_text(line.split(':', 1)[1])
        
        # Handle multi-line sections and sub-sections
        elif current_section == 'previous_history':
            if line.startswith('Past Medical History:'):
                clinical_data['medical_history']['past_medical_history'].append(clean_text(line.split(':', 1)[1]))
            elif line.startswith('Past Surgical History:'):
                clinical_data['medical_history']['past_surgical_history'].append(clean_text(line.split(':', 1)[1]))
            elif line.startswith('Family History:'):
                clinical_data['medical_history']['family_history'].append(clean_text(line.split(':', 1)[1]))
            elif line.startswith('Social History:'):
                clinical_data['medical_history']['social_history'].append(clean_text(line.split(':', 1)[1]))
        elif current_section == 'physical_exam' and line.startswith('General:'):
            clinical_data['examination']['physical_exam']['general'] = clean_text(line.split(':', 1)[1])
        elif current_section == 'vital_signs':
            vital_match = re.match(r'(\w+\s*\w*):\s*([^:]+)', line)
            if vital_match:
                key = vital_match.group(1).lower().replace(' ', '_')
                clinical_data['examination']['vital_signs'][key] = clean_text(vital_match.group(2))
        elif current_section in ['history_of_present_illness', 'review_of_systems', 'assessment', 'plan', 'decision_making']:
            # Append to the current section if it continues
            if current_section == 'history_of_present_illness':
                clinical_data['medical_history']['history_of_present_illness'] += ' ' + clean_text(line)
            elif current_section == 'review_of_systems':
                clinical_data['examination']['review_of_systems'] += ' ' + clean_text(line)
            elif current_section == 'assessment':
                clinical_data['assessment']['diagnosis'] += ' ' + clean_text(line)
            elif current_section == 'plan':
                clinical_data['plan']['treatment'] += ' ' + clean_text(line)
            elif current_section == 'decision_making':
                clinical_data['decision_making']['notes'] += ' ' + clean_text(line)
    
    return clinical_data

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
<<<<<<< HEAD
    instruction =  "Copilot you are a senior doctor in the medical field. You are aware that when we interact with patients it is mandatory to record the conversation in a way that is accurate and format medical notes that follws the standards outlined for all medical professions. These standards must note down every essential detail about the patient ,process and structure its information so it meets the medical health record standards. This record must be accurate and have the correct medical term in medical standard libraries and should be in a away that includes a standard of patient's meta data. So using this conversation that occurred between you and the patient draft a good medical report. Don't add any new information that's not included in the conversation, and don't make your own assumptions, just place the vital information from the conversation into accurate note structure: Clinical Note: Patient Name: <> Date of Birth: <> Age: <> Sex: <> Medical Record #: <> Date of clinic visit: <> Primary care provider: <> Personal note: <> History of Present Illness: <> Allergies: <> Medications: <> Previous History: Past Medical History: <> Past Surgical History: <> Family History: <> Social History: <> Review of Systems: <> Physical Exam: General appearance: <> Blood Pressure: <> Heart Rate: <> Respiratory Rate: <> Oxygen Saturation: <> Assessment: <> Plan: <> Medical Decision Making: <>\n\n"
=======
    print("Generating prompt")
    instruction = f"You are a senior doctor in the medical field. You are aware that when we interact with patients it is mandatory to record the conversation in a way that is accurate and format medical notes that follows the standards outlined for all medical professions. These standards must note down every essential detail about the patient, process and structure its information so it meets the medical health record standards. This record must be accurate and have the correct medical term in medical standard libraries and should be in a way that includes a standard of patient's metadata. So using this conversation that occurred between you and the patient draft a good medical report. Don't add any new information that's not included in the conversation, and don't make your own assumptions, just place the vital information from the conversation into accurate note structure. If the field doesn't have anything listed in the conversation leave it blank:\n\nClinical Note:\n\nPatient Name: <>\nDate of Birth: <>\nAge: <>\nSex: <>\nMedical Record #: <>\nDate of clinic visit: <>\nPrimary care provider: <>\nPersonal note: <>\n\nHistory of Present Illness: <>\nAllergies: <>\nMedications: <>\n\nPrevious History:\nPast Medical History: <>\nPast Surgical History: <>\nFamily History: <>\nSocial History: <>\n\nReview of Systems: <>\n\nPhysical Exam:\nGeneral appearance: <>\nBlood Pressure: <>\nHeart Rate: <>\nRespiratory Rate: <>\nOxygen Saturation: <>\n\nAssessment: <>\n\nPlan:\n<>\n\nMedical Decision Making:\n<> \n\n Possible ten illments <> (For this field list 10 possible illments that the patient might have given this medical history {transcript_data["medical_history"]}, only in this section). Use json formatting for the result and only return the json object."
>>>>>>> 7c3048942e4224657a2ad6c301092ebbff87bd77
    prompt = instruction + record(transcript_data)
    print("Sending prompt to Gemini API...")

    client = genai.Client(api_key="AIzaSyCjPdFvvzgMVGWN57axtKr_GAPVYlBtuBI")
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    response_text = response.text
    response_text = response_text.replace('```json', '').replace('```', '')
    try:
        response_text = json.loads(response_text)
    except json.JSONDecodeError as e:
        print("Failed to convert to json")
        pass

    # Clean response
    # pattern = r"\b(" + "|".join(text_to_remove) + r")\b"
    # response_text = re.sub(pattern, "", response_text, flags=re.IGNORECASE)
    # response_text = re.sub(r"\s+", " ", response_text).strip()
    
    print(type(response_text))
    # if not isinstance(response_text, str):
    #     raise ValueError("Failed to get valid text response from Gemini API")
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

        # Preparing files and data
        recordings_dir: str = os.path.join('patients', patient_id, 'recordings')
        medical_history_dir: str = os.path.join("Data", "clinical_note", "clinical_note_x1.txt")
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

        # Get medical history
        medical_history = None
        with open(medical_history_dir,"r") as f:
            file_content = f.read()
            file_content_json = clinical_note_to_json(file_content)
            
            transcript_data["medical_history"] = file_content_json["medical_history"].pop("history_of_present_illness")
            print(file_content_json["medical_history"])
            print("medical history added.")

        # Generate report
        medical_report = generate_medical_report(transcript_data)
        
        # Doctor patient conversation
        convo = []
        for utterance in transcript_data["utterances"]:
            convo.append({
                "speaker": utterance["speaker"],
                "text": utterance["text"]
            })

        # Cleanup
        os.remove(webm_path)
        os.remove(mp3_path)
        print(f"Deleted temp files: {webm_path}, {mp3_path}")

        print("Returning medical report")
<<<<<<< HEAD
        return jsonify({'medical_report': medical_report})
=======
        return jsonify({'medical_report': medical_report,
                        'dialog': convo})
>>>>>>> 7c3048942e4224657a2ad6c301092ebbff87bd77

    except Exception as e:
        print(f"Error in /api/transcribe: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=8000)
