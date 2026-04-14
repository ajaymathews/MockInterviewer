import os
import google.generativeai as genai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class AIBrain:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.or_api_key = os.getenv("OPENROUTER_API_KEY")
        self.use_openrouter = self.or_api_key and self.or_api_key != "YOUR_OPENROUTER_API_KEY"
        
        if self.use_openrouter:
            self.model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.or_api_key,
            )
            print(f"Using OpenRouter with model: {self.model_name}")
        else:
            self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            if self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
            else:
                self.model = None
            print(f"Using Google AI with model: {self.model_name}")
            
        self.chat_session = None
        self.history = []
        self.user_notes = ""
        try:
            for fname in ["sample_jd.txt", "sample.txt"]:
                if os.path.exists(fname):
                    with open(fname, "r", encoding="utf-8") as f:
                        self.user_notes = f.read()
                    break
        except:
            pass

    def start_interview(self, level, jd_text, cv_text, custom_questions="", tone="Calm"):
        # The tone is now passed in from main.py for UI sync
        
        # Level-specific instructions
        level_instructions = ""
        if level == "HR Level":
            level_instructions = """
            - Focus on cultural fit, soft skills, and how the candidate's background 'connects the dots' with the JD requirements.
            - Look for keyword matches between the CV and JD.
            - Ask about similar past experiences and situational behavioral questions.
            """
        elif level == "Technical Level":
            level_instructions = """
            - Focus on practical technical application and hands-on proficiency with the required tools/languages.
            - Ask about specific implementations, problem-solving approaches, and past technical challenges.
            """
        elif level == "Deep Technical Level":
            level_instructions = """
            - Focus on deep fundamentals, core concepts, and the 'whys' behind technical choices.
            - Dive deep into the complete technology stack mentioned in the JD.
            - Challenge the candidate's understanding of architecture, performance, and low-level details.
            """

        system_instruction = f"""
        You are an interviewer conducting a {level} interview with a {tone} tone.
        
        Job Description: {jd_text}
        Candidate's CV: {cv_text}
        Additional Context: {self.user_notes}
        
        Interview Focus ({level}):
        {level_instructions}
        
        Mandatory Questions to Include:
        {custom_questions if custom_questions else "No specific mandatory questions. Use your standard interview flow."}
        
        Rules:
        - Tone: Maintain a {tone} demeanor throughout.
        - Determine CV vs JD match percentage immediately and mention it subtly in the intro if possible.
        - Ask short, one-at-a-time technical and behavioral questions according to the {level} focus.
        - Be concise and push the candidate to elaborate on gaps.
        - Ensure all 'Mandatory Questions' listed above are asked at appropriate times during the interview.
        """
        
        self.history = [{"role": "system", "content": system_instruction}]
        
        if self.use_openrouter:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=self.history + [{"role": "user", "content": "Please start the interview."}]
                )
                reply = response.choices[0].message.content
                self.history.append({"role": "user", "content": "Please start the interview."})
                self.history.append({"role": "assistant", "content": reply})
                return reply
            except Exception as e:
                return f"OpenRouter Error: {str(e)}"
        else:
            if not self.model:
                return f"Hello, I am your {level} interviewer. (Running in demo mode - missing API key). Let's start: Please tell me about yourself?"
            try:
                self.chat_session = self.model.start_chat(history=[])
                response = self.chat_session.send_message(system_instruction + "\n\nPlease start the interview.")
                return response.text
            except Exception as e:
                return f"Interviewer Error: {str(e)}"
            
    def get_response(self, user_input, wrap_up=False):
        prompt = user_input + (" (Note: We are wrapping up, conclude firmly.)" if wrap_up else "")
        
        if self.use_openrouter:
            try:
                self.history.append({"role": "user", "content": prompt})
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=self.history
                )
                reply = response.choices[0].message.content
                self.history.append({"role": "assistant", "content": reply})
                return reply
            except Exception as e:
                return f"OpenRouter Error: {str(e)}"
        else:
            if not self.model or not self.chat_session:
                return f"Interesting point. Tell me more? (Demo Mode)"
            try:
                response = self.chat_session.send_message(prompt)
                return response.text
            except Exception as e:
                return f"AI Error: {str(e)}"

    def generate_content(self, prompt):
        """Unified method to generate content across providers."""
        if self.use_openrouter:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                return type('Response', (object,), {'text': response.choices[0].message.content})
            except Exception as e:
                return type('Response', (object,), {'text': f"Error: {str(e)}"})
        else:
            if not self.model:
                return type('Response', (object,), {'text': "Demo Mode Result"})
            try:
                return self.model.generate_content(prompt)
            except Exception as e:
                return type('Response', (object,), {'text': f"Error: {str(e)}"})

    def conduct_full_post_analysis(self, transcript, vision_log="No video data"):
        prompt = f"""
        The interview session has ended. Please provide a deep, comprehensive feedback report.
        
        FULL TRANSCRIPT:
        {transcript}
        
        VISUAL ANALYSIS REPORT:
        {vision_log}
        
        STRUCTURE YOUR FEEDBACK:
        1. Executive Summary (Overall performance score).
        2. Technical Proficiency (Depth of JD keyword coverage).
        3. Communication & Behavioral Analysis (Confidence, Filler words).
        4. Areas for Improvement (Specific gaps identified).
        5. Final Recommendation.
        """
        
        if self.use_openrouter:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"OpenRouter Analysis Error: {str(e)}"
        else:
            if not self.model:
                return f"Interview Analysis Complete.\nTranscript: {transcript[:100]}...\nVision: {vision_log}"
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                return f"Failed to generate deep analysis: {str(e)}"
