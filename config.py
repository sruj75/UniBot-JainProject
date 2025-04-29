"""
Configuration settings for the college chatbot application.
"""

# API Configuration
GROQ_API_KEY = "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"  # Groq API key
USE_GROQ = True  # Set to True to use Groq, False to use OpenAI or fallback to local models

# Model Configuration
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # Default Groq model (changed from llama3-70b-8192 for better compatibility)
FALLBACK_MODEL = "all-MiniLM-L6-v2"  # Local model for embeddings when no API key is available

# Vector Database Configuration
VECTOR_DB_PATH = "./chroma_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# UI Configuration
PAGE_TITLE = "College Information Chatbot"
PAGE_ICON = "🎓"
APP_TITLE = "College Information Assistant 🎓"
APP_SUBTITLE = "Upload your college PDF and ask questions about admissions, programs, campus life, and more!" 