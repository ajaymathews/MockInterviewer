import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont

class SetupWindow(QWidget):
    start_interview_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        # Title
        title = QLabel("AI Mock Interviewer Setup")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # Persona
        layout.addWidget(QLabel("Interview Level:"))
        self.level_cb = QComboBox()
        self.level_cb.addItems(["HR Level", "Technical Level", "Deep Technical Level"])
        layout.addWidget(self.level_cb)

        # JD
        layout.addWidget(QLabel("Paste Job Description:"))
        self.jd_input = QTextEdit()
        layout.addWidget(self.jd_input)

        # CV Upload
        cv_layout = QHBoxLayout()
        self.cv_btn = QPushButton("Upload CV (PDF)")
        self.cv_label = QLabel("No CV uploaded")
        self.cv_btn.clicked.connect(self.upload_cv)
        cv_layout.addWidget(self.cv_btn)
        cv_layout.addWidget(self.cv_label)
        layout.addLayout(cv_layout)
        self.cv_path = ""

        # Custom Questions
        layout.addWidget(QLabel("Custom Questions (AI will ask these):"))
        self.questions_input = QTextEdit()
        self.questions_input.setPlaceholderText("Enter specific questions you want the interviewer to ask...")
        layout.addWidget(self.questions_input)

        # Start
        self.start_btn = QPushButton("Start Interview")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 14px;")
        self.start_btn.clicked.connect(self.start_interview)
        layout.addWidget(self.start_btn)

        self.setLayout(layout)

    def upload_cv(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CV", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if file_path:
            self.cv_path = file_path
            self.cv_label.setText(file_path.split("/")[-1])

    def start_interview(self):
        # Default CV Logic
        if not self.cv_path:
            default_cv = r"Ajay_Mathews_CV_FWD.pdf"
            if os.path.exists(default_cv):
                self.cv_path = default_cv
                print(f"Using default CV: {default_cv}")
            else:
                QMessageBox.warning(self, "Missing CV", "No CV uploaded and default CV not found.")
                return

        if not self.jd_input.toPlainText():
            QMessageBox.warning(self, "Missing Data", "Please paste a Job Description.")
            return

        data = {
            "level": self.level_cb.currentText(),
            "jd": self.jd_input.toPlainText(),
            "cv_path": self.cv_path,
            "custom_questions": self.questions_input.toPlainText()
        }
        self.start_interview_signal.emit(data)
