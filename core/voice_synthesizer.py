import speech_recognition as sr
import threading
import pygame
import edge_tts
import asyncio
import tempfile
import os
import time

class VoiceSystem:
    def __init__(self):
        pygame.mixer.init()
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 2.0 # Slightly lower for faster turn-around
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
        self.voice_name = 'en-US-AriaNeural'
        self.is_speaking = False
        self.listening_enabled = True
        self.stop_listening = None

    def set_voice_gender(self, gender, persona="Calm"):
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
            # Temporarily disable background processing of spoken words to avoid echo
            self.listening_enabled = False 
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
                try: os.remove(temp_file)
                except: pass
            finally:
                self.is_speaking = False
                # Re-enable listening IMMEDIATELY
                self.listening_enabled = True
                if callback:
                    callback()

        threading.Thread(target=_speak_thread, daemon=True).start()

    def listen_continuous(self, callback_on_speech, stop_event):
        """Starts background listening that correctly handles the speaking state."""
        def internal_callback(recognizer, audio):
            if not self.listening_enabled or self.is_speaking:
                return # Ignore self-speech or disabled states
            
            try:
                text = recognizer.recognize_google(audio)
                if text:
                    callback_on_speech(text)
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"STT Error: {e}")

        # Start background listening
        m = sr.Microphone()
        with m as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
        
        self.stop_listening = self.recognizer.listen_in_background(m, internal_callback, phrase_time_limit=30)
        
        # Monitor stop_event to shut down
        def waiter():
            while not stop_event.is_set():
                time.sleep(0.5)
            if self.stop_listening:
                self.stop_listening(wait_for_stop=False)
        
        threading.Thread(target=waiter, daemon=True).start()
