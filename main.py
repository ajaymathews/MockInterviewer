import sys
import os
import random
import time
import threading
import cv2
import PyPDF2
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

        # Setup GUI Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.setup_win = SetupWindow()
        self.setup_win.start_interview_signal.connect(self.begin_interview)
        self.stack.addWidget(self.setup_win)

        self.interview_win = InterviewWindow(self.ai, self.voice, self.vision)
        # Instead of direct connect, route to main for logging
        self.interview_win.trigger_response_signal.connect(self.process_answer)
        self.interview_win.end_interview_signal.connect(self.end_interview_flow)
        self.interview_win.toggle_record_signal.connect(self.toggle_video_record)
        self.stack.addWidget(self.interview_win)

        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.check_time_constraints)
        
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self.record_frame)

    def extract_cv(self, filepath):
        try:
            reader = PyPDF2.PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error reading CV: {e}"

    def begin_interview(self, data):
        cv_text = self.extract_cv(data['cv_path'])
        jd_text = data['jd']
        persona = data['persona']
        # Randomize selection
        gender = random.choice(['Female', 'Male'])
        
        # Log init
        with open("interview_transcript.txt", "w") as f:
            f.write(f"--- Interview Started | Persona: {persona} | Gender: {gender} ---\n\n")

        self.voice.set_voice_gender(gender, persona)

        # Start Systems
        self.vision.start()
        self.interview_win.set_avatar(gender, persona)
        
        intro_text = self.ai.start_interview(persona, jd_text, cv_text)
        self.speak_and_log(intro_text)
        
        self.stack.setCurrentWidget(self.interview_win)
        self.start_time = time.time()
        self.is_wrapping_up = False
        self.session_timer.start(1000) # Check every second
        
        # Start Voice Activity Detection Loop
        self.vad_stop_event.clear()
        self.voice.listen_continuous(self.handle_vad_speech, self.vad_stop_event)

    def handle_vad_speech(self, text):
        # Called from background thread, switch to main thread safely via signal
        self.interview_win.trigger_response_signal.emit(text)

    def process_answer(self, text):
        if not text or text.startswith("["):
            return

        # Write to log and chat
        with open("interview_transcript.txt", "a") as f:
            f.write(f"You: {text}\n")
            
        self.interview_win.append_chat("You", text)
        
        # Get AI Response, include emotional telemetry
        current_emotion = self.vision.get_current_emotion()
        # If the final minute reached, signal AI to wrap up
        ai_reply = self.ai.get_response(text, current_emotion, wrap_up=self.is_wrapping_up)
        
        self.speak_and_log(ai_reply)

    def speak_and_log(self, text):
        with open("interview_transcript.txt", "a") as f:
            f.write(f"Interviewer: {text}\n\n")
        
        self.interview_win.append_chat("Interviewer", text)
        self.voice.speak(text)

    def check_time_constraints(self):
        elapsed = time.time() - self.start_time
        # 28 minutes = 1680 seconds
        if elapsed > 1680 and not self.is_wrapping_up:
            self.is_wrapping_up = True
            
        # 30 minutes = 1800 seconds
        if elapsed > 1800 and not self.voice.is_speaking:
            self.end_interview_flow()

    def toggle_video_record(self):
        if self.interview_win.is_recording_video:
            # Start
            frame = self.vision.get_current_frame()
            if frame is not None:
                h, w, _ = frame.shape
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter('interview_recording.mp4', fourcc, 20.0, (w, h))
                self.frame_timer.start(50) # 20 FPS
        else:
            # Stop
            self.frame_timer.stop()
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None

    def record_frame(self):
        if self.video_writer and self.interview_win.is_recording_video:
            frame = self.vision.get_current_frame()
            if frame is not None:
                # opencv writer expects BGR
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                self.video_writer.write(bgr_frame)

    def end_interview_flow(self):
        self.session_timer.stop()
        self.frame_timer.stop()
        self.vad_stop_event.set()
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            
        vision_log = self.vision.stop_and_report()
        feedback = self.ai.get_final_feedback(vision_log)
        
        with open("interview_feedback.txt", "w") as f:
            f.write(feedback)
        
        msg = QMessageBox()
        msg.setWindowTitle("Interview Feedback")
        msg.setText("Your Final Feedback Report has been saved to interview_feedback.txt!")
        msg.setDetailedText(feedback)
        msg.exec_()
        
        self.reset_app()

    def reset_app(self):
        self.stack.setCurrentWidget(self.setup_win)
        self.interview_win.chat_history.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MockInterviewerApp()
    window.show()
    sys.exit(app.exec_())
