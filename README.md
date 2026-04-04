# AI Mock Interviewer v2.0

An advanced, highly-sophisticated AI mock interviewer simulator built with PyQt5, Gemini Flash, deepface emotion telemetry, and Microsoft Edge Neural voices.

## Key Features
- **Zoom-Style Picture-in-Picture Interface**: Modern dark UI featuring simultaneous avatar rendering and webcam feed.
- **Hands-Free Conversational Voice Activity Detection**: Built-in VAD (Voice Activity Detection) constantly listens to your speech patterns. Pauses automatically submit your questions. No clicking required.
- **Natural Neural TTS**: Replaced robotic local TTS engines with `edge-tts` to utilize high-fidelity Microsoft Azure neural voices for Strict, Calm, and Friendly personas.
- **Adaptive Emotion Telemetry**: Leverages OpenCV and `deepface` to constantly read the candidate's facial expressions and feeds this context silently to the AI during the interview.
- **Session Timers**: 30-minute interview runtime constraints with AI-driven 28-minute firm wrap-ups.
- **Video Recording**: Record the interview locally frame-by-frame and export it to `.mp4` for self-review.
- **Evaluation Matrix Feedback**: Generates detailed behavioural evaluation reports post-interview.

## Environment Setup & Requirements

### Prerequisites
You need a `Python 3.9+` environment. The usage of [Conda](https://docs.conda.io/en/latest/) or `venv` is heavily recommended. You also require an active **Google Gemini API Key**.

### 1. Initialize Python Environment
If using Conda (as an example):
```bash
conda create --name mock_env python=3.9
conda activate mock_env
```

### 2. Install Dependencies
Make sure you are in the project's root folder where `requirements.txt` is located, then install the dependencies via `pip`:

```bash
pip install -r requirements.txt
```

*(Note: Depending on your OS, PyAudio might require underlying C dependencies. On Windows, PyAudio installs via pip without issue most of the time).*

**The exact `requirements.txt` list:**
```text
PyQt5
google-generativeai
opencv-python
deepface
SpeechRecognition
PyAudio
python-dotenv
PyPDF2
edge-tts
pygame
```

### 3. Setup Gemini API Key
Duplicate the `.env.example` file (or create your own `sample.txt`/`.env` file in the root):
```env
GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

### 4. Setup Avatar Assets
Ensure the `assets/avatars` folder contains your AI avatars named respectively (or run our built-in configuration):
```
/assets
  /avatars
    friendly_female.png
    strict_male.png
    calm_male.png
    calm_female.png
    friendly_male.png
    strict_female.png
```

## Running the Application

Once your virtual environment is active and requirements are installed, launch the app:

```bash
python main.py
```

### Usage Steps:
1. Select the Persona (Friendly, Calm, Strict).
2. Paste the **Job Description** you are practicing for.
3. Upload your **CV/Resume as a PDF**.
4. Press **Start Interview**. The engine will randomize the gender, configure the respective Neural voice mappings, and launch the Zoom-UI.
5. The interview listens dynamically. Start talking immediately when it's your turn.
6. Check `interview_transcript.txt` and `interview_feedback.txt` after ending the call for your logs.
