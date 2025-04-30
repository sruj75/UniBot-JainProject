"""
Configuration settings for the college chatbot application.
"""
import os
import streamlit as st

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Detect if running in Streamlit Cloud
IS_STREAMLIT_CLOUD = os.environ.get('STREAMLIT_SHARING', '') == 'true'

# API Configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")  # Groq API key
USE_GROQ = True  # Set to True to use Groq, False to use OpenAI or fallback to local models

# Model Configuration
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # Default Groq model
FALLBACK_MODEL = "all-MiniLM-L6-v2"  # Local model for embeddings when no API key is available

# Vector Database Configuration
# Use different storage strategies depending on deployment environment
if IS_STREAMLIT_CLOUD:
    # In Streamlit Cloud, use a directory that gets recreated each session
    VECTOR_DB_PATH = "/tmp/chroma_db"  # Temporary directory in Streamlit Cloud
else:
    # For local development, use a persistent directory
    VECTOR_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

# The key is used to ensure the vector database is created once per session
VECTOR_DB_KEY = "vector_db_created"

# Flag to track when we're using the in-memory fallback solution
USING_IN_MEMORY_DB = False

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# UI Configuration
PAGE_TITLE = "College Information Chatbot"
PAGE_ICON = "🎓"
APP_TITLE = "College Information Assistant 🎓"
APP_SUBTITLE = "Ask questions about B.Tech/M.Tech programs at Jain University" 