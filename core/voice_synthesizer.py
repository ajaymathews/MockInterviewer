import speech_recognition as sr
import threading
import pygame
import edge_tts
import asyncio
import tempfile
import os

class VoiceSystem:
    def __init__(self):
        pygame.mixer.init()
        self.recognizer = sr.Recognizer()
        self.voice_name = 'en-US-AriaNeural' # Default
        self.is_speaking = False
        
    def set_voice_gender(self, gender, persona="Calm"):
        # Map persona and gender to edge-tts voices
        if gender.lower() == 'female':
            if persona.lower() == 'strict':
                self.voice_name = 'en-US-AriaNeural'
            elif persona.lower() == 'calm':
                self.voice_name = 'en-US-JennyNeural'
            else:
                self.voice_name = 'en-US-AnaNeural'
        else:
            if persona.lower() == 'strict':
                self.voice_name = 'en-US-ChristopherNeural'
            elif persona.lower() == 'calm':
                self.voice_name = 'en-US-BrianNeural'
            else:
                self.voice_name = 'en-US-GuyNeural'

    def speak(self, text, callback=None):
        def _speak_thread():
            self.is_speaking = True
            try:
                temp_file = tempfile.mktemp(suffix='.mp3')
                async def _generate():
                    communicate = edge_tts.Communicate(text, self.voice_name)
                    await communicate.save(temp_file)
                    
                asyncio.run(_generate())
                
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    
                pygame.mixer.music.unload()
                try:
                    os.remove(temp_file)
                except:
                    pass
            finally:
                self.is_speaking = False
                if callback:
                    callback()

        threading.Thread(target=_speak_thread, daemon=True).start()

    def listen_continuous(self, callback_on_speech, stop_event):
        def _listen_worker():
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                while not stop_event.is_set():
                    if self.is_speaking:
                        pygame.time.Clock().tick(10)
                        continue
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=30)
                        if not self.is_speaking:  # Double check
                            text = self.recognizer.recognize_google(audio)
                            if text:
                                callback_on_speech(text)
                    except sr.WaitTimeoutError:
                        pass
                    except sr.UnknownValueError:
                        pass
                    except Exception as e:
                        print(f"VAD Error: {e}")
                        
        t = threading.Thread(target=_listen_worker, daemon=True)
        t.start()
        return t
