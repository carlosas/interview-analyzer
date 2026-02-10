import os
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from openai import OpenAI

class LLMService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # Initialize the OpenAI client for transcription (Whisper)
        self.client = OpenAI(api_key=self.openai_api_key)

    def transcribe_audio(self, file_path):
        """
        Transcribes an audio file using OpenAI's Whisper model.
        """
        with open(file_path, "rb") as audio_file:
            transcription_response = self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcription_response.text

    def analyze_interview(self, transcription, system_prompt, context_text=None):
        """
        Analyzes the interview transcription using a ChatOpenAI model.
        """
        chat_model = ChatOpenAI(model="gpt-4o", temperature=0.5, api_key=self.openai_api_key)
        
        user_content = f"Transcript:\n{transcription}"
        if context_text:
             user_content = f"Context (e.g. CV):\n{context_text}\n\n" + user_content

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]
        response = chat_model.invoke(messages)
        return response.content
