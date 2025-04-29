import streamlit as st
import os
import time
from dotenv import load_dotenv
from pdf_processor import process_pdf, create_vector_db
from chatbot import get_response
import config

# Load environment variables
load_dotenv()

# Set up the page
st.set_page_config(
    page_title="College PDF Chatbot",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
    }
    .subheader {
        font-size: 1.2rem;
        color: #4B5563;
    }
    .groq-badge {
        background-color: #581c87;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: bold;
        display: inline-block;
        margin-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Default PDF directory
PDF_DIR = "docs"
DEFAULT_PDF = os.path.join(PDF_DIR, "BTech_MTech_2022.pdf")

# Header
st.markdown("<h1 class='main-header'>College Information Chatbot 🎓</h1>", unsafe_allow_html=True)
st.markdown("<p class='subheader'>Ask questions about the college based on the PDF information</p>", unsafe_allow_html=True)

# Show model info if Groq is enabled
if config.USE_GROQ:
    st.markdown(f"<p>Powered by <span class='groq-badge'>Groq {config.DEFAULT_MODEL}</span></p>", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
    
if "current_pdf" not in st.session_state:
    st.session_state.current_pdf = None

# Main content area
col1, col2 = st.columns([3, 1])

with col1:
    # Display welcome message if no conversation yet
    if not st.session_state.messages:
        st.info("👋 Welcome! Select a PDF and process it to start asking questions.")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about the college...", disabled=not st.session_state.pdf_processed):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                try:
                    start_time = time.time()
                    response = get_response(prompt, [(m["role"], m["content"]) for m in st.session_state.messages[:-1] if m["role"] in ["user", "assistant"]])
                    response_time = time.time() - start_time
                    
                    st.write(response)
                    st.caption(f"Response time: {response_time:.2f} seconds")
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
                    response = "I'm sorry, I encountered an error. Please try again."
                    st.write(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

with col2:
    st.sidebar.title("PDF Selection")
    
    # Find all PDFs in the docs directory
    pdf_files = []
    if os.path.exists(PDF_DIR):
        for file in os.listdir(PDF_DIR):
            if file.lower().endswith('.pdf'):
                pdf_files.append(file)
    
    # Display PDF options
    selected_pdf = st.sidebar.selectbox(
        "Choose a PDF file",
        pdf_files,
        index=0 if pdf_files else None,
        format_func=lambda x: f"{x} ({os.path.getsize(os.path.join(PDF_DIR, x)) / (1024*1024):.1f} MB)"
    )
    
    if selected_pdf:
        pdf_path = os.path.join(PDF_DIR, selected_pdf)
        
        # Process button
        if st.sidebar.button(f"Process {selected_pdf}"):
            with st.sidebar.spinner(f"Processing {selected_pdf}..."):
                try:
                    # Process the PDF
                    start_time = time.time()
                    text = process_pdf(pdf_path)
                    create_vector_db(text)
                    processing_time = time.time() - start_time
                    
                    # Update session state
                    st.session_state.pdf_processed = True
                    st.session_state.current_pdf = selected_pdf
                    
                    # Success message
                    st.sidebar.success(f"PDF processed in {processing_time:.2f} seconds!")
                    st.sidebar.info(f"You can now ask questions about {selected_pdf}")
                    
                    # Clear previous chat
                    st.session_state.messages = []
                    st.experimental_rerun()
                except Exception as e:
                    st.sidebar.error(f"Error processing PDF: {str(e)}")
    
    # Display current PDF info
    if st.session_state.pdf_processed and st.session_state.current_pdf:
        st.sidebar.subheader("Current PDF")
        st.sidebar.info(st.session_state.current_pdf)
        
        # Add sample questions based on the PDF content
        st.sidebar.subheader("Sample Questions")
        
        if "BTech" in st.session_state.current_pdf or "MTech" in st.session_state.current_pdf:
            sample_questions = [
                "What are the admission requirements?",
                "How many branches are offered?",
                "What is the fee structure?",
                "What scholarships are available?",
                "What is the placement record?"
            ]
        elif "handbook" in st.session_state.current_pdf.lower():
            sample_questions = [
                "What are the university rules?",
                "What are the attendance requirements?",
                "What facilities are available on campus?",
                "What extracurricular activities are offered?",
                "What is the examination system?"
            ]
        else:
            sample_questions = [
                "What programs are offered?",
                "Tell me about the university",
                "What are the admission criteria?",
                "What is the campus like?",
                "How can I apply?"
            ]
        
        for question in sample_questions:
            if st.sidebar.button(question):
                # Add the question to chat
                st.session_state.messages.append({"role": "user", "content": question})
                st.experimental_rerun()
    
    # Add some helpful information
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Tips for better results:")
    st.sidebar.markdown("• Ask specific questions about programs, admissions, etc.")
    st.sidebar.markdown("• If you don't get a good answer, try rephrasing")
    st.sidebar.markdown("• Longer documents take more time to process") 