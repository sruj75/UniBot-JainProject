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
    page_title="College Information Chatbot",
    page_icon="🎓"
)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False

if "messages" not in st.session_state:
    st.session_state.messages = []

# Default PDF settings
PDF_DIR = "docs"
DEFAULT_PDF = os.path.join(PDF_DIR, "BTech_MTech_2022.pdf")  # Change this to your preferred default PDF

# Header
st.title("College Information Chatbot 🎓")
st.write("Ask questions about the college based on the PDF information")

# Auto-initialize on first load
if not st.session_state.initialized:
    with st.spinner("Setting up the chatbot... Please wait."):
        try:
            # Process the default PDF
            if os.path.exists(DEFAULT_PDF):
                text = process_pdf(DEFAULT_PDF)
                create_vector_db(text)
                st.session_state.initialized = True
                st.session_state.pdf_name = os.path.basename(DEFAULT_PDF)
                st.success(f"Ready! Using information from: {os.path.basename(DEFAULT_PDF)}")
            else:
                # If default PDF doesn't exist, try to find any PDF in the directory
                pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
                if pdf_files:
                    alt_pdf = os.path.join(PDF_DIR, pdf_files[0])
                    text = process_pdf(alt_pdf)
                    create_vector_db(text)
                    st.session_state.initialized = True
                    st.session_state.pdf_name = pdf_files[0]
                    st.success(f"Ready! Using information from: {pdf_files[0]}")
                else:
                    st.error("No PDF files found in the docs directory.")
        except Exception as e:
            st.error(f"Error initializing: {str(e)}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Add a horizontal line for better separation
st.markdown("---")

# Sample questions section (collapsible)
with st.expander("Sample Questions (click to expand)"):
    # Determine sample questions based on the PDF file
    if hasattr(st.session_state, 'pdf_name') and st.session_state.pdf_name:
        if "BTech" in st.session_state.pdf_name or "MTech" in st.session_state.pdf_name:
            sample_questions = [
                "What are the admission requirements?",
                "How many branches are offered?",
                "What is the fee structure?",
                "What scholarships are available?",
                "What is the placement record?"
            ]
        elif "handbook" in st.session_state.pdf_name.lower():
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
        
        # Create buttons for sample questions
        cols = st.columns(2)
        for i, question in enumerate(sample_questions):
            if cols[i % 2].button(question):
                # Add the question to chat
                st.session_state.messages.append({"role": "user", "content": question})
                st.experimental_rerun()

# Chat input section
if st.session_state.initialized:
    if prompt := st.chat_input("Ask a question about the college..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                try:
                    response = get_response(prompt, [(m["role"], m["content"]) for m in st.session_state.messages[:-1] if m["role"] in ["user", "assistant"]])
                    st.write(response)
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
                    response = "I'm sorry, I encountered an error. Please try again."
                    st.write(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("The chatbot is being initialized. Please wait...")

# Footer
st.markdown("---")
st.caption(f"Using information from: {st.session_state.pdf_name if hasattr(st.session_state, 'pdf_name') else 'No PDF loaded'}")
if config.USE_GROQ:
    st.caption(f"Powered by Groq ({config.DEFAULT_MODEL})")
else:
    st.caption("Powered by local models") 