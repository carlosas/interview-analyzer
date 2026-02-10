from database import Database
import os

# Ensure environment variables are set or default to localhost for testing
if not os.getenv("DB_HOST"):
    os.environ["DB_HOST"] = "localhost"
if not os.getenv("DB_USER"):
    os.environ["DB_USER"] = "postgres"
if not os.getenv("DB_PASS"):
    os.environ["DB_PASS"] = "postgres"
if not os.getenv("DB_NAME"):
    os.environ["DB_NAME"] = "postgres"

try:
    db = Database()
    print("Connected to DB")

    # Insert mock data
    print("Inserting data...")
    id1 = db.save_transcription(
        "mock_interview_1.mp3", "This is a transcript of interview 1.\nInterviewer: Tell me about yourself.\nCandidate: I am a software engineer.")
    db.update_analysis(
        id1, "## Analysis\n**Strength:** Good communication.\n**Weakness:** Talked too fast.")

    id2 = db.save_transcription(
        "mock_interview_2.mp3", "This is a transcript of interview 2.\nInterviewer: What is your greatest weakness?\nCandidate: Kryptonite.")
    db.update_analysis(
        id2, "## Analysis\n**Strength:** Honest.\n**Weakness:** Not human.")

    print(f"Inserted mock data with IDs: {id1}, {id2}")
except Exception as e:
    print(f"Error: {e}")
