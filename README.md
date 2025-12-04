# Medi-Mate: Medical Prescription RAG 🏥💊

**Medi-Mate** is an intelligent Retrieval-Augmented Generation (RAG) application designed to help users manage and understand their medical prescriptions. Built with **Streamlit**, **Google Gemini**, and **Pinecone**, it allows users to upload prescriptions, ask questions, and even schedule medicine reminders directly to their Google Calendar.

![Medi-Mate Demo](https://github.com/Shreeehe/Medi-Mate/raw/refs/heads/main/Sample.mp4)

## 🌟 Features

*   **📄 Prescription Ingestion**: Upload PDF or Image prescriptions. The app extracts text, medicines, and dosage instructions using **Gemini 2.5 Flash Lite**.
*   **💬 RAG-Powered Chat**: Ask questions about your prescriptions (e.g., "When should I take Amoxicillin?"). The app retrieves relevant context from the vector store to provide accurate answers.
*   **🧠 Contextual Memory**: Remembers your chat history for each prescription.
*   **⚡ Token Optimization**: Automatically removes stop words from chat history to save tokens and reduce latency.
*   **📅 Google Calendar Integration**: Add medicine schedules to your Google Calendar with a single click.
*   **🌐 Multi-Language Support**: Interact with the app in **English, Hindi, Tamil, Kannada, Malayalam, or Telugu**.
*   **🔐 User Authentication**: Secure login and registration system.

## 🛠️ Tech Stack

*   **Frontend**: Streamlit
*   **LLM & Embedding**: Google Gemini 2.5 Flash Lite (`gemini-2.5-flash-lite`, `text-embedding-004`)
*   **Vector Database**: Pinecone
*   **Application Database**: MongoDB (Atlas)
*   **Orchestration**: LangGraph
*   **Language**: Python 3.12+

## 🚀 Installation & Setup

### Prerequisites
*   Python 3.10 or higher
*   **Google Cloud API Key** (for Gemini)
*   **Pinecone API Key**
*   **MongoDB Connection String**
*   **Google Cloud OAuth Credentials** (for Calendar integration)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/medi-mate.git
cd medi-mate
```

### 2. Install Dependencies
Using `uv` (recommended) or `pip`:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```ini
GOOGLE_API_KEY=your_google_api_key
PINECONE_API_KEY=your_pinecone_api_key
MONGO_URI=your_mongodb_uri
```

### 4. Google Calendar Setup
1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a project and enable the **Google Calendar API**.
3.  Create **OAuth 2.0 Client IDs** (Application type: **Desktop app**).
4.  Download the JSON file, rename it to `credentials.json`, and place it in the project root.

### 5. Run the Application
```bash
streamlit run app.py
```

## 📖 Usage Guide

1.  **Login/Register**: Create an account to save your data.
2.  **Upload**: Use the sidebar to upload a prescription (PDF/Image).
3.  **Chat**:
    *   The app will extract and index the data.
    *   Ask questions like "What are the side effects?" or "How many days should I take this?".
    *   Select your preferred **Language** from the sidebar settings.
4.  **Calendar**:
    *   Expand the **"💊 Medicine Details"** section.
    *   Click **"📅 Add to Google Calendar"** to schedule reminders.

## 📂 Project Structure

```
medi-mate/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── credentials.json       # Google OAuth credentials (DO NOT COMMIT)
├── .env                   # Environment variables (DO NOT COMMIT)
├── src/
│   ├── auth.py            # User authentication logic
│   ├── calendar_utils.py  # Google Calendar API manager
│   ├── config.py          # Configuration settings
│   ├── extractor.py       # Gemini extraction logic
│   ├── graph.py           # LangGraph RAG workflow
│   ├── ingestion.py       # File processing
│   ├── memory.py          # MongoDB memory manager
│   ├── utils.py           # Utility functions (logger, stop words)
│   └── vector_store.py    # Pinecone vector store manager
└── data/                  # Temporary data storage
```

## 🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## 📄 License
This project is licensed under the MIT License.


