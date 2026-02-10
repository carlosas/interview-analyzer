import os
from database import Database
from services.llm_service import LLMService

class InterviewOrchestrator:
    def __init__(self):
        self.db = Database()
        self.llm_service = LLMService()

    def get_all_interviews(self):
        return self.db.get_all_interviews()

    def get_interview(self, interview_id):
        return self.db.get_interview(interview_id)

    def get_all_cvs(self):
        return self.db.get_all_cvs()

    def get_cv(self, cv_id):
        return self.db.get_cv(cv_id)

    def process_new_interview(self, file_name, file_content, system_prompt, cv_context=None):
        """
        Orchestrates the upload, transcription, persistence, and analysis of a new interview.
        Returns the new interview_id upon success.
        """
        # Save file temporarily
        file_path = f"temp_{file_name}"
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 1. Transcribe
            transcription_text = self.llm_service.transcribe_audio(file_path)
            
            # 2. Save initial transcription to DB
            interview_id = self.db.save_transcription(system_prompt, file_name, transcription_text)
            
            if not interview_id:
                raise Exception("Failed to save transcription to database.")

            # 3. Analyze
            analysis_text = self.llm_service.analyze_interview(transcription_text, system_prompt, cv_context)
            
            # 4. Update DB with analysis
            self.db.update_analysis(interview_id, analysis_text, system_prompt)
            
            return interview_id
            
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    def reanalyze_interview(self, interview_id, transcription_text, new_prompt, cv_context=None):
        """
        Re-runs the analysis on an existing transcription.
        """
        new_analysis = self.llm_service.analyze_interview(transcription_text, new_prompt, cv_context)
        self.db.update_analysis(interview_id, new_analysis, new_prompt)
        return new_analysis

    def delete_interview(self, interview_id):
        return self.db.delete_interview(interview_id)
