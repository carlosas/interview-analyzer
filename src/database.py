import os
import psycopg2
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
        self.init_db()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
            )
        except Exception as e:
            print(f"Database connection failed: {e}")
            self.conn = None

    def init_db(self):
        if not self.conn:
            return
        
        query_interviews = """
        CREATE TABLE IF NOT EXISTS interviews (
            id SERIAL PRIMARY KEY,
            audio_filename TEXT NOT NULL,
            analysis_prompt TEXT,
            transcription TEXT,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        query_cvs = """
        CREATE TABLE IF NOT EXISTS cvs (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query_interviews)
                cur.execute(query_cvs)
            self.conn.commit()
        except Exception as e:
            print(f"Error initializing DB: {e}")
            self.conn.rollback()

    def save_transcription(self, analysis_prompt, filename, text):
        if not self.conn:
            return None
        
        query = """
        INSERT INTO interviews (analysis_prompt, audio_filename, transcription)
        VALUES (%s, %s, %s)
        RETURNING id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (analysis_prompt, filename, text))
                interview_id = cur.fetchone()[0]
            self.conn.commit()
            return interview_id
        except Exception as e:
            print(f"Error saving transcription: {e}")
            self.conn.rollback()
            return None

    def update_analysis(self, interview_id, analysis_text, analysis_prompt=None):
        if not self.conn:
            return
        
        query = """
        UPDATE interviews
        SET analysis = %s, analysis_prompt = %s
        WHERE id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (analysis_text, analysis_prompt, interview_id))
            self.conn.commit()
        except Exception as e:
            print(f"Error updating analysis: {e}")
            self.conn.rollback()


    def get_interview(self, interview_id):
        if not self.conn:
            return None
            
        # Explicitly select columns to ensure consistent indexing in main.py
        # 0: id, 1: filename, 2: transcription, 3: analysis, 4: prompt, 5: created_at
        query = """
        SELECT id, audio_filename, transcription, analysis, analysis_prompt, created_at 
        FROM interviews 
        WHERE id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (interview_id,))
                return cur.fetchone()
        except Exception as e:
            print(f"Error getting interview: {e}")
            return None

    def get_all_interviews(self):
        if not self.conn:
            return []
            
        query = "SELECT id, audio_filename, created_at FROM interviews ORDER BY created_at DESC;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(f"Error getting all interviews: {e}")
            return []

    def delete_interview(self, interview_id):
        if not self.conn:
            return False
            
        query = "DELETE FROM interviews WHERE id = %s;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (interview_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting interview: {e}")
            self.conn.rollback()
            return False

    def save_cv(self, name, filename):
        if not self.conn:
            return None
        
        query = """
        INSERT INTO cvs (name, filename)
        VALUES (%s, %s)
        RETURNING id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (name, filename))
                cv_id = cur.fetchone()[0]
            self.conn.commit()
            return cv_id
        except Exception as e:
            print(f"Error saving CV: {e}")
            self.conn.rollback()
            return None

    def get_all_cvs(self):
        if not self.conn:
            return []
            
        query = "SELECT id, name, filename, created_at FROM cvs ORDER BY created_at DESC;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(f"Error getting all CVs: {e}")
            return []

    def delete_cv(self, cv_id):
        if not self.conn:
            return False
            
        query = "DELETE FROM cvs WHERE id = %s;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (cv_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting CV: {e}")
            self.conn.rollback()
            return False
