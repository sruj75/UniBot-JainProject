import streamlit as st
import os
import time
import traceback
from dotenv import load_dotenv
from pdf_processor import process_pdf, extract_with_pypdf, extract_with_pymupdf, create_vector_db
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
DEFAULT_PDF = os.path.join(PDF_DIR, "BTech_MTech_2022.pdf")  # The specific PDF we want to use
FALLBACK_PDFS = [
    os.path.join(PDF_DIR, "student-handbook-2018-2019-jain-university.pdf"),
    os.path.join(PDF_DIR, "Jain Shaata.pdf")
]

# Header
st.title("UniBot")
st.write("Ask questions about B.Tech and M.Tech programs")

# Function to try extracting text from a PDF
def try_extract_text(pdf_path):
    try:
        # First method
        try:
            text = process_pdf(pdf_path)
            st.info(f"Extracted {len(text)} characters with process_pdf")
            if text and len(text.strip()) > 100:
                return text
        except Exception as e:
            st.warning(f"process_pdf failed: {str(e)}")
        
        # Second method
        try:
            text = extract_with_pypdf(pdf_path)
            st.info(f"Extracted {len(text)} characters with PyPDF")
            if text and len(text.strip()) > 100:
                return text
        except Exception as e:
            st.warning(f"PyPDF extraction failed: {str(e)}")
        
        # Third method
        try:
            text = extract_with_pymupdf(pdf_path)
            st.info(f"Extracted {len(text)} characters with PyMuPDF")
            if text and len(text.strip()) > 100:
                return text
        except Exception as e:
            st.warning(f"PyMuPDF extraction failed: {str(e)}")
        
        return None
    except Exception as e:
        st.error(f"Error in extraction: {str(e)}")
        return None

# Auto-initialize on first load
if not st.session_state.initialized:
    with st.spinner("Setting up the chatbot... Please wait."):
        try:
            # Get all PDF files
            all_pdfs = [DEFAULT_PDF] + FALLBACK_PDFS
            
            # Try each PDF until one works
            text = None
            used_pdf = None
            
            for pdf_path in all_pdfs:
                if os.path.exists(pdf_path):
                    st.info(f"Trying PDF file: {os.path.basename(pdf_path)}")
                    extracted_text = try_extract_text(pdf_path)
                    
                    if extracted_text and len(extracted_text.strip()) > 100:
                        text = extracted_text
                        used_pdf = pdf_path
                        break
                else:
                    st.warning(f"PDF file not found: {pdf_path}")
            
            # If we have text, create the vector database
            if text and used_pdf:
                # Create vector database
                create_vector_db(text)
                st.session_state.initialized = True
                st.session_state.pdf_name = os.path.basename(used_pdf)
                st.success(f"Ready! Using information from: {os.path.basename(used_pdf)}")
            else:
                # Show all files in the directory
                pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
                if pdf_files:
                    st.error("Failed to extract text from any PDF files. They might be scanned or secured.")
                    st.info(f"Available PDF files in {PDF_DIR}:")
                    for pdf_file in pdf_files:
                        st.info(f"- {pdf_file}")
                else:
                    st.error(f"No PDF files found in {PDF_DIR}")
        except Exception as e:
            st.error(f"Error initializing: {str(e)}")
            st.code(traceback.format_exc())

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Add a horizontal line for better separation
st.markdown("---")

# Chat input section
if st.session_state.initialized:
    if prompt := st.chat_input("Ask a question about B.Tech/M.Tech programs..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    start_time = time.time()
                    response = get_response(prompt, [(m["role"], m["content"]) for m in st.session_state.messages[:-1] if m["role"] in ["user", "assistant"]])
                    end_time = time.time()
                    st.write(response)
                    st.caption(f"Response time: {end_time - start_time:.2f} seconds")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    response = "I'm sorry, I encountered an error. Please try again."
                    st.write(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Use st.rerun() to refresh the UI with the new messages
        st.rerun()
else:
    st.info("The chatbot is being initialized. Please wait...")

# Footer
st.markdown("---")
if st.session_state.initialized:
    st.caption(f"Information source: {st.session_state.pdf_name}")

if config.USE_GROQ:
    st.caption(f"Powered by Groq ({config.DEFAULT_MODEL})")
else:
    st.caption("Powered by local models") 