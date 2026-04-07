import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class AIBrain:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash') # Use flash for speed
        else:
            self.model = None
            
        self.chat_session = None
        self.user_notes = ""
        try:
            # Try sample_jd.txt first as per user's latest preference for default JD/notes
            for fname in ["sample_jd.txt", "sample.txt"]:
                if os.path.exists(fname):
                    with open(fname, "r") as f:
                        self.user_notes = f.read()
                    break
        except:
            pass

    def start_interview(self, persona, jd_text, cv_text):
        if not self.model:
            return f"Hello, I am your {persona} interviewer. (Running in demo mode - missing API key). Let's start: Please tell me about yourself?"
            
        system_instruction = f"""
        You are a {persona} job interviewer. 
        Job Description: {jd_text}
        Candidate's CV: {cv_text}
        Additional Context: {self.user_notes}
        
        Rules:
        - Determine CV vs JD match percentage immediately.
        - Ask short, one-at-a-time technical and behavioral questions.
        - Be concise and push the candidate to elaborate on gaps.
        """
        
        try:
            self.chat_session = self.model.start_chat(history=[])
            response = self.chat_session.send_message(system_instruction + "\n\nPlease start the interview.")
            return response.text
        except Exception as e:
            return f"Interviewer Error: {str(e)}"
            
    def get_response(self, user_input, wrap_up=False):
        if not self.model or not self.chat_session:
            return f"Interesting point. Tell me more? (Demo Mode)"
            
        try:
            prompt = user_input + (" (Note: We are wrapping up, conclude firmly.)" if wrap_up else "")
            response = self.chat_session.send_message(prompt)
            return response.text
        except Exception as e:
            return f"AI Error: {str(e)}"

    def conduct_full_post_analysis(self, transcript, vision_log="No video data"):
        """
        Performs a comprehensive analysis of the entire interview.
        """
        if not self.model:
            return f"Interview Analysis Complete.\nTranscript: {transcript[:100]}...\nVision: {vision_log}"
            
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
        try:
            # Use a fresh request for analysis to avoid history constraints
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Failed to generate deep analysis: {str(e)}"
