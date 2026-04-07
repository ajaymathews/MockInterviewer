import os
import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import QTimer, Qt, pyqtSignal

class InterviewWindow(QWidget):
    end_interview_signal = pyqtSignal()
    trigger_response_signal = pyqtSignal(str)
    toggle_record_signal = pyqtSignal()
    manual_submit_signal = pyqtSignal()

    def __init__(self, ai_brain, voice_sys, vision_sys):
        super().__init__()
        self.ai = ai_brain
        self.voice = voice_sys
        self.vision = vision_sys
        self.is_recording_manual = False # User manually clicked record
        self.blink_state = False
        self.blink_counter = 0
        self.initUI()
        
    def initUI(self):
        # Professional Deep Black Theme
        self.setStyleSheet("""
            QWidget { 
                background-color: #000000; 
                color: #ffffff; 
                font-family: 'Segoe UI', Arial;
            }
            QTextEdit {
                background-color: #0a0a0a;
                color: #e0e0e0;
                font-size: 14px;
                border: 1px solid #1a1a1a;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton {
                background-color: #1a1a1a;
                color: white;
                padding: 8px 20px;
                font-size: 14px;
                border-radius: 5px;
                border: 1px solid #333333;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
            QPushButton#endBtn {
                background-color: #E02828;
                border: none;
                font-weight: bold;
            }
            QPushButton#endBtn:hover {
                background-color: #B22020;
            }
            QPushButton#recordBtn[active="true"] {
                background-color: #E02828;
                color: white;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 0)
        main_layout.setSpacing(15)

        # Video Area
        self.video_layout = QHBoxLayout()
        self.video_layout.setSpacing(15)
        
        self.avatar_label = QLabel("Interviewer")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("border: 1px solid #1a1a1a; border-radius: 10px; background-color: #050505;")
        self.video_layout.addWidget(self.avatar_label, stretch=2)

        self.camera_label = QLabel("Webcam")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("border: 1px solid #1a1a1a; border-radius: 10px; background-color: #050505;")
        self.video_layout.addWidget(self.camera_label, stretch=2)

        main_layout.addLayout(self.video_layout, stretch=5)

        # Chat History
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        main_layout.addWidget(self.chat_history, stretch=2)

        # Bottom Control Bar
        control_bar_container = QWidget()
        control_bar_container.setStyleSheet("background-color: #0a0a0a; border-top: 1px solid #1a1a1a;")
        control_bar_layout = QHBoxLayout(control_bar_container)
        control_bar_layout.setContentsMargins(20, 15, 20, 15)
        
        self.mic_status = QLabel("🎤 Listening")
        self.mic_status.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        control_bar_layout.addWidget(self.mic_status)
        
        control_bar_layout.addSpacing(20)
        
        self.submit_btn = QPushButton("Submit Now")
        self.submit_btn.setMinimumHeight(40)
        self.submit_btn.clicked.connect(self.manual_submit_signal.emit)
        control_bar_layout.addWidget(self.submit_btn)

        control_bar_layout.addStretch(1)

        self.record_btn = QPushButton("⏺ Record Interview")
        self.record_btn.setObjectName("recordBtn")
        self.record_btn.setProperty("active", "false")
        self.record_btn.setMinimumHeight(40)
        self.record_btn.clicked.connect(self.toggle_recording)
        control_bar_layout.addWidget(self.record_btn)

        control_bar_layout.addSpacing(10)

        self.end_btn = QPushButton("Leave Interview")
        self.end_btn.setObjectName("endBtn")
        self.end_btn.setMinimumHeight(40)
        self.end_btn.clicked.connect(self.end_interview_signal.emit)
        control_bar_layout.addWidget(self.end_btn)
        
        main_layout.addWidget(control_bar_container)
        self.setLayout(main_layout)

        # Update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(50)

    def set_avatar(self, gender, persona):
        cwd = os.getcwd()
        persona_lower = persona.lower()
        if gender.lower() == 'female':
            if persona_lower == 'strict': path = os.path.join(cwd, 'assets', 'avatars', 'strict_female.png')
            elif persona_lower == 'calm': path = os.path.join(cwd, 'assets', 'avatars', 'calm_female.png')
            else: path = os.path.join(cwd, 'assets', 'avatars', 'friendly_female.png')
        else:
            if persona_lower == 'strict': path = os.path.join(cwd, 'assets', 'avatars', 'strict_male.png')
            elif persona_lower == 'calm': path = os.path.join(cwd, 'assets', 'avatars', 'calm_male.png')
            else: path = os.path.join(cwd, 'assets', 'avatars', 'friendly_male.png')
                
        if os.path.exists(path):
            pixmap = QPixmap(path)
            self.avatar_label.setPixmap(pixmap.scaled(600, 600, Qt.KeepAspectRatio))
        else:
            self.avatar_label.setText(f"Avatar missing: {persona}")

    def update_ui(self):
        frame = self.vision.get_current_frame()
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(q_img).scaled(600, 600, Qt.KeepAspectRatio))

        if self.voice.is_speaking:
            self.mic_status.setText("🔊 Speaking")
            self.mic_status.setStyleSheet("color: #2D8CFF; font-weight: bold;")
            self.submit_btn.setEnabled(False)
            self.video_layout.setStretchFactor(self.avatar_label, 3)
            self.video_layout.setStretchFactor(self.camera_label, 1)
            self.camera_label.setStyleSheet("border: 1px solid #1a1a1a; border-radius: 10px;")
            self.blink_state = False
        else:
            self.mic_status.setText("🎤 Listening")
            self.mic_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.submit_btn.setEnabled(True)
            self.video_layout.setStretchFactor(self.avatar_label, 1)
            self.video_layout.setStretchFactor(self.camera_label, 3)
            
            # Blinking indicator logic
            self.blink_counter += 50
            if self.blink_counter >= 500:
                self.blink_state = not self.blink_state
                self.blink_counter = 0
            
            if self.blink_state:
                self.camera_label.setStyleSheet("border: 3px solid #0E72ED; border-radius: 10px;")
            else:
                self.camera_label.setStyleSheet("border: 1px solid #1a1a1a; border-radius: 10px;")

    def append_chat(self, speaker, text):
        color = "#4CAF50" if speaker == "You" else "#2D8CFF"
        self.chat_history.append(f"<b style='color: {color};'>{speaker}:</b> {text}<br>")
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

    def toggle_recording(self):
        self.is_recording_manual = not self.is_recording_manual
        self.record_btn.setProperty("active", "true" if self.is_recording_manual else "false")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
        self.record_btn.setText("⏹ Stop Manual Recording" if self.is_recording_manual else "⏺ Record Interview")
        self.toggle_record_signal.emit()
