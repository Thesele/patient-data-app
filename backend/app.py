# # backend/app.py
# from fastapi import FastAPI
# from pydantic import BaseModel
# import requests
# import time
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# # Allow frontend requests
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # your frontend URL
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# ASSEMBLY_AI_KEY = "your_assembly_ai_key"

# class TranscriptionRequest(BaseModel):
#     audioUrl: str
#     patientId: str

# @app.post("/transcribe")
# def transcribe(data: TranscriptionRequest):
#     # 1. Send audio URL to Assembly AI
#     headers = {"authorization": ASSEMBLY_AI_KEY, "content-type": "application/json"}
#     response = requests.post(
#         "https://api.assemblyai.com/v2/transcript",
#         headers=headers,
#         json={"audio_url": data.audioUrl}
#     )
#     transcript_id = response.json()["id"]

#     # 2. Poll for completion
#     while True:
#         result = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers).json()
#         if result["status"] == "completed":
#             return {"transcript": result["text"]}
#         elif result["status"] == "failed":
#             return {"transcript": ""}
#         time.sleep(2)
