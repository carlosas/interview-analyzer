# Interview-Analyzer

<img src="assets/logo.png" align="right" width="100" alt="Interview-Analyzer Logo">

> 🚧 **WORK IN PROGRESS** 🚧

Interview-Analyzer is a tiny application designed to help you analyze and improve your job interview performance. It leverages AI to transcribe and analyze your interview recordings, providing actionable feedback.

---

![example new analysis](assets/example_new_analysis.png)
_Interface for uploading and analyzing a new interview._

---

![example analyzed interview](assets/example_analyzed_interview.png)
_Detailed analysis and feedback view._

---

## Features

- **AI-Powered Analysis**: Automatically evaluates your interview performance using advanced LLMs.
- **Transcription**: seamlessly converts audio recordings into text for review.
- **Historical Analysis**: Keeps a record of your past interviews and analyses for tracking progress.
- **Secure Access**: Simple username/password authentication to protect your data.
- **Interactive Feedback**: Re-analyze specific parts or ask follow-up questions about your performance.

## Tech Stack

This project is built using a modern, robust stack:

- **[Streamlit](https://streamlit.io/)**: For building the interactive web interface.
- **[LangChain](https://www.langchain.com/)**: To orchestrate the LLM interactions and analysis logic.
- **[PostgreSQL](https://www.postgresql.org/)**: For persistent storage of transcripts and analysis results.
- **[Docker](https://www.docker.com/)**: For consistent environment and easy deployment.

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your machine.
- An OpenAI API Key.

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository_url>
   cd interview-analyzer
   ```

2. **Configure Environment Variables:**
   Copy the example environment file:

   ```bash
   cp .env.dist .env
   ```

   Open `.env` and fill in the required values:
   - `OPENAI_API_KEY`: Your OpenAI API key.
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`: Database credentials.
   - `LOGIN_USER`, `LOGIN_PASSWORD`: Credentials to log in to the app.

3. **Start the Application:**
   Run the following command to build and start the services:
   ```bash
   docker-compose up --build
   ```

## Usage

1. Open your browser and navigate to `http://localhost:8501`.
2. Log in using the credentials you defined in `.env`.
3. **Analyze New Interview**: Go to the main page to upload an audio file. The system will transcribe and analyze it.
4. **View History**: Use the sidebar to navigate to past interviews and review the AI's feedback.

## Database Management

The project includes **Adminer** for easy database management.

- Access Adminer at `http://localhost:8080`.
- System: PostgreSQL.
- Server: `db`.
- Username/Password/Database: As defined in your `.env` file.
