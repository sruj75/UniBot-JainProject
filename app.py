import streamlit as st
import os
import time
import traceback
from dotenv import load_dotenv
from pdf_processor import create_vector_db
from chatbot import get_response
import config

# Load environment variables
load_dotenv()

# Print important paths for debugging
print(f"Current working directory: {os.getcwd()}")
print(f"Vector DB path: {config.VECTOR_DB_PATH}")
print(f"Vector DB path exists: {os.path.exists(config.VECTOR_DB_PATH)}")
print(f"Running in Streamlit Cloud: {config.IS_STREAMLIT_CLOUD}")

# Set up the page
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON
)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.loading = True
    st.session_state.error_message = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# The vector_db_created key is used to ensure the database is created only once per session
if config.VECTOR_DB_KEY not in st.session_state:
    st.session_state[config.VECTOR_DB_KEY] = False

# Header
st.title("UniBot")
st.write("Ask questions about B.Tech and M.Tech programs")

# Auto-initialize on first load
if not st.session_state.initialized:
    # Hide all the loading messages with a simple progress spinner
    with st.spinner("Loading chatbot, please wait..."):
        try:
            # Always recreate the vector database in Streamlit Cloud
            # In local mode, we'll only create it if it doesn't exist
            if config.IS_STREAMLIT_CLOUD or not os.path.exists(config.VECTOR_DB_PATH) or not st.session_state[config.VECTOR_DB_KEY]:
                # Create vector database directly with built-in sample data
                print("Creating vector database with sample college data")
                create_vector_db()
                st.session_state[config.VECTOR_DB_KEY] = True
            else:
                print("Using existing vector database")
            
            # Mark initialization as complete
            print("Vector database is ready for use")
            st.session_state.initialized = True
            st.session_state.loading = False
            st.session_state.source_name = "College Program Information"
        except Exception as e:
            print(f"Initialization error: {e}")
            traceback.print_exc()
            st.session_state.loading = False
            st.session_state.error_message = f"Error initializing: {str(e)}"

# Only display the chat interface when fully initialized
if st.session_state.initialized:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Add a horizontal line for better separation
    st.markdown("---")
    
    # Chat input section
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
    
    # Footer
    st.markdown("---")
    st.caption(f"Information source: {st.session_state.source_name}")
    
    if config.USE_GROQ:
        st.caption(f"Powered by Groq ({config.DEFAULT_MODEL})")
    else:
        st.caption("Powered by local models")
elif st.session_state.loading:
    # Simple loading message while initializing
    st.info("Initializing chatbot...")
elif st.session_state.error_message:
    # Display error message
    st.error(st.session_state.error_message)
    st.button("Retry initialization", on_click=lambda: st.session_state.update({"initialized": False, "loading": True, "error_message": None})) 