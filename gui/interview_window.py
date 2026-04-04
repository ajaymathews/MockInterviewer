import os
import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import QTimer, Qt, pyqtSignal

class InterviewWindow(QWidget):
    end_interview_signal = pyqtSignal()
    trigger_response_signal = pyqtSignal(str)
    toggle_record_signal = pyqtSignal()

    def __init__(self, ai_brain, voice_sys, vision_sys):
        super().__init__()
        self.ai = ai_brain
        self.voice = voice_sys
        self.vision = vision_sys
        self.is_recording_video = False
        self.initUI()
        
    def initUI(self):
        # Dark Theme Background
        self.setStyleSheet("background-color: #1c1c1c; color: #ffffff;")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Video Grid
        video_layout = QHBoxLayout()
        
        # Avatar Feed
        self.avatar_label = QLabel("Loading Avatar...")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("border: 2px solid #555555; background-color: #000000;")
        video_layout.addWidget(self.avatar_label, stretch=2)

        # Webcam Feed
        self.camera_label = QLabel("Webcam Feed Offline")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("border: 2px solid #555555; background-color: #000000;")
        video_layout.addWidget(self.camera_label, stretch=2)

        main_layout.addLayout(video_layout, stretch=4)

        # Chat History (subtitles style)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("background-color: #2a2a2a; color: #e0e0e0; font-size: 14px; border: none; padding: 10px;")
        main_layout.addWidget(self.chat_history, stretch=1)

        # Bottom Control Bar
        control_bar_layout = QHBoxLayout()
        control_bar_layout.addStretch(1)

        self.mic_status = QLabel("🎤 Listening (Auto-Speech)")
        self.mic_status.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 16px; margin-right: 20px;")
        control_bar_layout.addWidget(self.mic_status)

        self.record_btn = QPushButton("🔴 Record Video")
        self.record_btn.setStyleSheet("background-color: #ff9800; color: white; padding: 10px 20px; font-size: 14px; border-radius: 5px;")
        self.record_btn.clicked.connect(self.toggle_recording)
        control_bar_layout.addWidget(self.record_btn)

        self.end_btn = QPushButton("End Interview")
        self.end_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px 20px; font-size: 14px; border-radius: 5px;")
        self.end_btn.clicked.connect(self.end_interview)
        control_bar_layout.addWidget(self.end_btn)
        
        control_bar_layout.addStretch(1)

        main_layout.addLayout(control_bar_layout)
        self.setLayout(main_layout)

        # Timer to update Webcam feed from OpenCV
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_webcam)
        self.timer.start(50)

    def set_avatar(self, gender, persona):
        cwd = os.getcwd()
        persona_lower = persona.lower()
        if gender.lower() == 'female':
            if persona_lower == 'strict':
                path = os.path.join(cwd, 'assets', 'avatars', 'strict_female.png')
            elif persona_lower == 'calm':
                path = os.path.join(cwd, 'assets', 'avatars', 'calm_female.png')
            else:
                path = os.path.join(cwd, 'assets', 'avatars', 'friendly_female.png')
        else:
            if persona_lower == 'strict':
                path = os.path.join(cwd, 'assets', 'avatars', 'strict_male.png')
            elif persona_lower == 'calm':
                path = os.path.join(cwd, 'assets', 'avatars', 'calm_male.png')
            else:
                path = os.path.join(cwd, 'assets', 'avatars', 'friendly_male.png')
                
        if os.path.exists(path):
            pixmap = QPixmap(path)
            self.avatar_label.setPixmap(pixmap.scaled(600, 600, Qt.KeepAspectRatio))
        else:
            self.avatar_label.setText(f"Avatar Asset Missing: {path}")

    def update_webcam(self):
        frame = self.vision.get_current_frame()
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(q_img).scaled(600, 600, Qt.KeepAspectRatio))

    def append_chat(self, speaker, text):
        self.chat_history.append(f"<b style='color: #4CAF50;'>{speaker}:</b> {text}<br>")
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

    def speak_and_log(self, text):
        self.append_chat("Interviewer", text)
        self.voice.speak(text)

    def process_user_answer(self, text):
        if not text or text.startswith("["):
            return

        self.append_chat("You", text)
        
        # Inform AI Brain
        ai_reply = self.ai.get_response(text)
        self.speak_and_log(ai_reply)

    def toggle_recording(self):
        self.is_recording_video = not self.is_recording_video
        if self.is_recording_video:
            self.record_btn.setText("⏹ Stop Recording")
            self.record_btn.setStyleSheet("background-color: #d32f2f; color: white; padding: 10px 20px; font-size: 14px; border-radius: 5px;")
        else:
            self.record_btn.setText("🔴 Record Video")
            self.record_btn.setStyleSheet("background-color: #ff9800; color: white; padding: 10px 20px; font-size: 14px; border-radius: 5px;")
        self.toggle_record_signal.emit()

    def end_interview(self):
        self.end_interview_signal.emit()
