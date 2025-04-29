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
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
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
    .success-msg {
        padding: 10px;
        background-color: #D1FAE5;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .stChatMessage {
        background-color: #F9FAFB;
        padding: 0.5rem;
    }
    .user-bubble {
        background-color: #DBEAFE;
        padding: 10px;
        border-radius: 10px;
    }
    .assistant-bubble {
        background-color: #F3F4F6;
        padding: 10px;
        border-radius: 10px;
    }
    .highlight {
        background-color: #FEF3C7;
        padding: 5px;
        border-radius: 3px;
        font-weight: bold;
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

# Header
st.markdown(f"<h1 class='main-header'>{config.APP_TITLE}</h1>", unsafe_allow_html=True)
st.markdown(f"<p class='subheader'>{config.APP_SUBTITLE}</p>", unsafe_allow_html=True)

# Show Groq badge if enabled
if config.USE_GROQ:
    st.markdown(f"<p>Powered by <span class='groq-badge'>Groq {config.DEFAULT_MODEL}</span> for lightning-fast responses</p>", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False

# Sidebar for PDF upload
with st.sidebar:
    st.header("Upload College PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", help="Upload a PDF document containing information about your college")
    
    if uploaded_file is not None:
        # Save the uploaded file
        with open("college_info.pdf", "wb") as f:
            f.write(uploaded_file.getvalue())
        
        st.success("PDF uploaded successfully!")
        
        # Process the PDF
        if st.button("Process PDF", help="Extract information from the PDF and make it searchable"):
            with st.spinner("Processing PDF... This may take a moment"):
                try:
                    # Process the PDF and create vector database
                    start_time = time.time()
                    text = process_pdf("college_info.pdf")
                    create_vector_db(text)
                    processing_time = time.time() - start_time
                    
                    st.session_state.pdf_processed = True
                    st.success(f"PDF processed in {processing_time:.2f} seconds and ready for questions!")
                    st.markdown("<div class='success-msg'>✅ PDF has been processed successfully. You can now ask questions about the content!</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
                    st.info("Please try a different PDF or check if the file is valid.")
    
    # Add some helpful information
    st.markdown("---")
    st.markdown("### Tips for better results:")
    st.markdown("• Upload a detailed college brochure or prospectus")
    st.markdown("• Ask specific questions about programs, admissions, campus facilities, etc.")
    st.markdown("• If you don't get a satisfactory answer, try rephrasing your question")
    
    if config.USE_GROQ:
        st.markdown("---")
        st.markdown("✅ Using Groq API for enhanced responses")
    elif os.getenv("OPENAI_API_KEY"):
        st.markdown("---")
        st.markdown("✅ Using OpenAI for enhanced responses")
    else:
        st.markdown("---")
        st.markdown("ℹ️ For better quality answers, add your OpenAI or Groq API key to a .env file")

# Main chat interface
col1, col2 = st.columns([2, 1])

with col1:
    # Display welcome message if no conversation yet
    if not st.session_state.messages:
        st.info("👋 Welcome! Upload and process a college PDF, then ask questions about the college.")

    # Display chat messages
    for i, message in enumerate(st.session_state.messages):
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
            with st.spinner("Thinking..." if not config.USE_GROQ else "Generating response with Groq..."):
                try:
                    start_time = time.time()
                    response = get_response(prompt, [(m["role"], m["content"]) for m in st.session_state.messages[:-1] if m["role"] in ["user", "assistant"]])
                    response_time = time.time() - start_time
                    
                    st.write(response)
                    
                    if config.USE_GROQ:
                        st.caption(f"Response generated in {response_time:.2f} seconds using Groq")
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
                    response = "I'm sorry, I encountered an error. Please try again or upload a different PDF."
                    st.write(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

with col2:
    # Only show this section if PDF has been processed
    if st.session_state.pdf_processed:
        st.markdown("### Sample Questions")
        sample_questions = [
            "What programs are offered?",
            "What are the admission requirements?",
            "Tell me about campus facilities",
            "What scholarships are available?",
            "How is student life on campus?",
            "What is the application deadline?"
        ]
        
        for question in sample_questions:
            if st.button(question):
                # Add the question to chat
                st.session_state.messages.append({"role": "user", "content": question})
                
                # Skip to bottom and reload
                st.experimental_rerun() 