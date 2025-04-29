import streamlit as st
import os
import time
from dotenv import load_dotenv
from pdf_processor import process_pdf, extract_with_pypdf, extract_with_pymupdf
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from chatbot import get_response
import config

# Load environment variables
load_dotenv()

# Set up the page
st.set_page_config(
    page_title="College Chatbot",
    page_icon="🎓"
)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False

if "messages" not in st.session_state:
    st.session_state.messages = []

# Default PDF settings
PDF_DIR = "docs"

# Header
st.title("College Information Chatbot 🎓")
st.write("Ask any questions about the college")

# Function to extract text from all PDFs
def process_all_pdfs(dir_path):
    all_text = ""
    processed_files = []
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.pdf')]
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(dir_path, pdf_file)
        try:
            # Try to extract text
            text = extract_with_pypdf(pdf_path)
            
            # If text extraction failed or got minimal text, try alternate method
            if not text or len(text.strip()) < 100:
                try:
                    # Try to import and use PyMuPDF as a fallback
                    text = extract_with_pymupdf(pdf_path)
                except ImportError:
                    continue  # Skip this file if can't extract
            
            # Add to combined text
            all_text += f"\n\n--- FROM {pdf_file} ---\n\n"
            all_text += text
            processed_files.append(pdf_file)
            
        except Exception as e:
            st.warning(f"Could not process {pdf_file}: {str(e)}")
    
    return all_text, processed_files

# Function to create vector DB from combined text
def create_combined_vector_db(text):
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    # Create embeddings
    try:
        # Try to use OpenAI embeddings if API key is available
        if os.getenv("OPENAI_API_KEY"):
            embeddings = OpenAIEmbeddings()
        else:
            # Fall back to local embeddings model
            embeddings = HuggingFaceEmbeddings(model_name=config.FALLBACK_MODEL)
    except Exception as e:
        # Always fall back to local embeddings if there's an issue
        embeddings = HuggingFaceEmbeddings(model_name=config.FALLBACK_MODEL)
    
    # Create vector database directory if it doesn't exist
    os.makedirs(config.VECTOR_DB_PATH, exist_ok=True)
    
    # Create and persist vector database
    vectordb = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=config.VECTOR_DB_PATH
    )
    
    # Persist the database
    vectordb.persist()

# Auto-initialize on first load
if not st.session_state.initialized:
    with st.spinner("Setting up the chatbot... This might take a minute as we process all PDF files."):
        try:
            # Process all PDFs
            combined_text, processed_files = process_all_pdfs(PDF_DIR)
            
            if combined_text:
                # Create vector DB from combined text
                create_combined_vector_db(combined_text)
                st.session_state.initialized = True
                st.session_state.pdf_files = processed_files
                st.success(f"Ready! Processed {len(processed_files)} PDF files.")
            else:
                st.error("No PDF content could be extracted. Please check your PDF files.")
        except Exception as e:
            st.error(f"Error initializing: {str(e)}")
            st.error("Try refreshing the page to initialize again.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Add a horizontal line for better separation
st.markdown("---")

# Sample questions section
if st.session_state.initialized:
    sample_questions = [
        "What are the admission requirements?",
        "What programs are offered?",
        "Tell me about the university",
        "What is the fee structure?",
        "What scholarships are available?",
        "What are the attendance requirements?",
        "What facilities does the campus have?",
        "How can I apply?"
    ]
    
    # Create buttons for sample questions
    st.subheader("Try asking:")
    
    # Create 2 columns for the buttons
    cols = st.columns(2)
    for i, question in enumerate(sample_questions):
        if cols[i % 2].button(question):
            # Add the question to chat
            st.session_state.messages.append({"role": "user", "content": question})
            st.experimental_rerun()

# Chat input section
if st.session_state.initialized:
    if prompt := st.chat_input("Ask a question..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = get_response(prompt, [(m["role"], m["content"]) for m in st.session_state.messages[:-1] if m["role"] in ["user", "assistant"]])
                    st.write(response)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    response = "I'm sorry, I encountered an error. Please try again."
                    st.write(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("The chatbot is being initialized. Please wait...")

# Footer
if st.session_state.initialized and hasattr(st.session_state, 'pdf_files'):
    with st.expander("Information sources"):
        for pdf in st.session_state.pdf_files:
            st.write(f"- {pdf}")
    
if config.USE_GROQ:
    st.caption(f"Powered by Groq ({config.DEFAULT_MODEL})")
else:
    st.caption("Powered by local models") 