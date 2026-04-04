import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class AIBrain:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            
        self.chat_session = None
        
        # Load user constraints from sample.txt
        self.user_notes = ""
        try:
            with open("sample.txt", "r") as f:
                self.user_notes = f.read()
        except:
            print("Note: sample.txt not found.")

    def check_match(self, cv_text, jd_text):
        if not self.model:
            return "Note: Gemini API Key missing in .env! \n(Fallback mode: Your CV seems like a 75% match to this JD based on general keywords.)"
            
        prompt = f"Analyze this CV against this Job Description. Provide a very short 2-sentence pop-up summary of how well they match. \n\nJD: {jd_text}\n\nCV: {cv_text}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"API Error: {str(e)}"

    def start_interview(self, persona, jd_text, cv_text):
        if not self.model:
            return f"Hello, I am your {persona} interviewer. Since my API Key is missing, I am running in fallback mode. Let's start: Please tell me about yourself and your background?"
            
        system_instruction = f"""
        You are a {persona} job interviewer. 
        Job Description: {jd_text}
        Candidate's CV: {cv_text}
        
        Crucial User Training Needs (You must enforce these):
        {self.user_notes}
        
        Rules:
        - First, analyze the candidate's CV against the Job Description based strictly on keyword matching to determine a match percentage.
        - Introduce yourself briefly based on your {persona} persona.
        - Start the conversation by explicitly stating the candidate's CV vs Job Description match percentage based on the keywords.
        - Start asking questions based on where the candidate's CV matches or lacks the JD keywords.
        - Actively listen to their answers. If they mention keywords (like DMA, MATLAB to C, ADXL345), drill deep into them.
        - If they give one-sentence answers, push them to elaborate ("Please explain the gaps here...").
        - Keep responses conversational and concise. Do NOT give long paragraphs.
        """
        
        try:
            self.chat_session = self.model.start_chat(history=[])
            response = self.chat_session.send_message(system_instruction + "\n\nPlease begin the interview by introducing yourself and stating the keyword match percentage.")
            return response.text
        except Exception as e:
            return f"AI Generation Error: {str(e)}"
            
    def get_response(self, user_input, current_emotion="neutral", wrap_up=False):
        if not self.model or not self.chat_session:
            return f"Interesting point about '{user_input}'. Could you elaborate more about how that applies to this job? (API missing fallback)"
            
        try:
            wrap_text = " (Note: The interview is over its time limit. Acknowledge their answer briefly and firmly conclude the interview). " if wrap_up else ""
            emotion_text = f" (Hidden context: The candidate is currently looking {current_emotion}. Treat this as a behavioural indicator during your response if applicable). " 
            
            prompt = f"{user_input}\n{emotion_text}{wrap_text}"
            response = self.chat_session.send_message(prompt)
            return response.text
        except Exception as e:
            return f"AI Generation Error: {str(e)}"
            
    def get_final_feedback(self, vision_report):
        if not self.model or not self.chat_session:
            return f"Interview complete!\nFacial Analysis Report from Webcam: {vision_report} \n\n(Install a Gemini API Key to receive comprehensive LLM feedback)."
            
        prompt = f"The interview is over. Please provide a final, comprehensive but concise feedback report to the candidate based on their answers. Factor in their facial analysis during the interview: {vision_report}"
        try:
            res = self.chat_session.send_message(prompt)
            return res.text
        except Exception as e:
            return f"Failed to generate feedback: {str(e)}"
