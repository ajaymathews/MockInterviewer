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
        layout.addWidget(QLabel("Interviewer Persona:"))
        self.persona_cb = QComboBox()
        self.persona_cb.addItems(["Friendly", "Calm", "Strict"])
        layout.addWidget(self.persona_cb)

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
        if not self.jd_input.toPlainText() or not self.cv_path:
            QMessageBox.warning(self, "Missing Data", "Please paste a JD and upload a CV.")
            return

        data = {
            "persona": self.persona_cb.currentText(),
            "jd": self.jd_input.toPlainText(),
            "cv_path": self.cv_path
        }
        self.start_interview_signal.emit(data)
