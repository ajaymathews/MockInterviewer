import cv2
import threading
import time

try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None

class VisionAnalyzer:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.emotion_log = []
        self.current_frame = None

    def start(self):
        self.cap = cv2.VideoCapture(0)
        self.is_running = True
        self.thread = threading.Thread(target=self._update_frame, daemon=True)
        self.thread.start()
        
        if DeepFace:
            self.eval_thread = threading.Thread(target=self._evaluate_emotion, daemon=True)
            self.eval_thread.start()

    def _update_frame(self):
        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
            time.sleep(0.05)

    def _evaluate_emotion(self):
        while self.is_running:
            if self.current_frame is not None:
                try:
                    # Analyze emotions periodically
                    res = DeepFace.analyze(self.current_frame, actions=['emotion'], enforce_detection=False)
                    if isinstance(res, list):
                        res = res[0]
                    dominant = res.get('dominant_emotion', 'neutral')
                    self.emotion_log.append(dominant)
                    self.current_emotion = dominant
                except Exception as e:
                    pass
            time.sleep(2.0)

    def get_current_emotion(self):
        return getattr(self, 'current_emotion', 'neutral')

    def get_current_frame(self):
        if self.current_frame is not None:
            return cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        return None

    def stop_and_report(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        
        if not self.emotion_log:
            return "Facial tracking was inactive or lacked permission."
        
        calm_emotions = ['happy', 'neutral', 'surprise']
        nervous_emotions = ['sad', 'fear', 'angry', 'disgust']
        
        calm_count = sum(1 for e in self.emotion_log if e in calm_emotions)
        total = len(self.emotion_log)
        confidence = (calm_count / total) * 100 if total > 0 else 0
        
        return f"Facial Confidence Tracker: You appeared confident/calm {confidence:.0f}% of the time. Monitored emotional shifts: {list(set(self.emotion_log))}."
