import sys
import os
import time
import threading
import shutil
import cv2
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtCore import QTimer

from core.ai_brain import AIBrain
from core.voice_synthesizer import VoiceSystem
from core.camera_vision import VisionAnalyzer
from gui.setup_window import SetupWindow
from gui.interview_window import InterviewWindow

class MockInterviewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Mock Interviewer Pro")
        self.resize(1200, 800)
        
        # Initialize Core Systems
        self.ai = AIBrain()
        self.voice = VoiceSystem()
        self.vision = VisionAnalyzer()

        self.vad_stop_event = threading.Event()
        self.start_time = 0
        self.is_wrapping_up = False
        self.video_writer = None
        self.temp_video_path = ""
        self.temp_transcript_path = ""
        self.job_role = "Job_Role"

        # Setup GUI Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.setup_win = SetupWindow()
        # Default JD from sample_jd.txt
        if os.path.exists("sample_jd.txt"):
            with open("sample_jd.txt", "r") as f:
                self.setup_win.jd_input.setText(f.read())
        
        self.setup_win.start_interview_signal.connect(self.begin_interview)
        self.stack.addWidget(self.setup_win)

        self.interview_win = InterviewWindow(self.ai, self.voice, self.vision)
        self.interview_win.trigger_response_signal.connect(self.process_answer)
        self.interview_win.end_interview_signal.connect(self.end_interview_flow)
        self.stack.addWidget(self.interview_win)

        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self.record_frame)

    def extract_cv(self, path):
        if path.endswith('.pdf'):
            try:
                import PyPDF2
                text = ""
                with open(path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages: text += page.extract_text()
                return text
            except: return "PDF Extraction Failed"
        return "Manual Entry"

    def begin_interview(self, data):
        cv_text = self.extract_cv(data['cv_path'])
        jd_text = data['jd']
        level = data['level']
        custom_questions = data.get('custom_questions', '')
        
        # Extract job role for naming
        self.job_role = "Interview"
        try:
            res = self.ai.generate_content(f"Extract job title from: {jd_text[:300]}. Return only the title.")
            if res and res.text:
                self.job_role = res.text.strip().replace(' ', '_').replace('/', '_')
        except: pass

        # Folders setup
        os.makedirs("transcripts/temp", exist_ok=True)
        os.makedirs("recordings", exist_ok=True)
        
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        self.temp_video_path = f"transcripts/temp/temp_video_{date_str}.mp4"
        self.temp_transcript_path = f"transcripts/temp/temp_trans_{date_str}.txt"
        
        # Initialize temp transcript
        with open(self.temp_transcript_path, "w") as f:
            f.write(f"--- Interview Started: {datetime.now()} ---\n\n")

        # Start Vision & Recording
        self.vision.start()
        self.start_video_writer(self.temp_video_path)
        
        import random
        tone = random.choice(["Friendly", "Calm", "Strict"])
        self.voice.set_voice_gender(random_gender(), tone) 
        self.interview_win.set_avatar("Male", tone) 
        
        intro = self.ai.start_interview(level, jd_text, cv_text, custom_questions, tone=tone)
        self.speak_and_log(intro)
        
        self.stack.setCurrentWidget(self.interview_win)
        self.start_time = time.time()
        
        # Start Background Listener
        self.vad_stop_event.clear()
        self.voice.listen_continuous(self.handle_speech, self.vad_stop_event)

    def start_video_writer(self, path):
        # We need a frame to get the size
        frame = self.vision.get_current_frame()
        if frame is not None:
            h, w, _ = frame.shape
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(path, fourcc, 20.0, (w, h))
            self.record_timer.start(50) # 20 FPS

    def record_frame(self):
        if self.video_writer:
            frame = self.vision.get_current_frame()
            if frame is not None:
                self.video_writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    def handle_speech(self, text):
        text_lower = text.lower()
        stop_phrases = ["stop the interview", "wind up the interview", "terminate the session", "let's windup", "finish the interview"]
        
        if any(phrase in text_lower for phrase in stop_phrases):
            self.interview_win.append_chat("System", "End command detected. Processing final feedback...")
            # Schedule end on main thread
            QTimer.singleShot(100, self.end_interview_flow)
            return

        self.interview_win.trigger_response_signal.emit(text)

    def process_answer(self, text):
        if not text: return
        with open(self.temp_transcript_path, "a") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] You: {text}\n")
        self.interview_win.append_chat("You", text)
        
        # Immediate Processing
        reply = self.ai.get_response(text)
        self.speak_and_log(reply)

    def speak_and_log(self, text):
        with open(self.temp_transcript_path, "a") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Interviewer: {text}\n\n")
        self.interview_win.append_chat("Interviewer", text)
        self.voice.speak(text)

    def end_interview_flow(self):
        self.record_timer.stop()
        self.vad_stop_event.set()
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.vision.stop()
        
        # Perform Synthesis
        self.interview_win.mic_status.setText("⏳ Generating Feedback...")
        
        with open(self.temp_transcript_path, "r") as f:
            full_transcript = f.read()
            
        # Optional video analysis
        vision_report = self.vision.perform_post_analysis(self.temp_video_path)
        feedback = self.ai.conduct_full_post_analysis(full_transcript, vision_report)
        
        # Save Final Files
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        base_name = f"{self.job_role}_{date_str}"
        final_trans = os.path.join("transcripts", f"{base_name}_trans.txt")
        final_fb = os.path.join("transcripts", f"{base_name}_fb.txt")
        
        shutil.copy(self.temp_transcript_path, final_trans)
        with open(final_fb, "w") as f: f.write(feedback)
        
        # Manual Recording Logic
        if self.interview_win.is_recording_manual:
            perm_video = os.path.join("recordings", f"{base_name}_recording.mp4")
            shutil.copy(self.temp_video_path, perm_video)
            QMessageBox.information(self, "Recording Saved", f"A permanent copy of the interview was saved to recordings/ folder.")
        
        # Cleanup temp
        try: os.remove(self.temp_video_path)
        except: pass
        
        QMessageBox.information(self, "Interview Complete", f"Feedback report saved as {os.path.basename(final_fb)}")
        self.reset_app()

    def reset_app(self):
        self.stack.setCurrentWidget(self.setup_win)
        self.interview_win.chat_history.clear()

def random_gender():
    import random
    return random.choice(["Male", "Female"])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MockInterviewerApp()
    window.show()
    sys.exit(app.exec_())
