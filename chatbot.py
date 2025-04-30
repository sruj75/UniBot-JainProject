import os
import traceback
import groq
import openai
import streamlit as st
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from langchain_community.llms import HuggingFaceHub
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import config

# Get API keys - first try environment variables, then Streamlit secrets
def get_api_key(key_name, default=None):
    # First try environment variables
    value = os.environ.get(key_name)
    if value:
        return value
    
    # Then try Streamlit secrets
    try:
        return st.secrets.get(key_name, default)
    except:
        return default

# Initialize Groq client
groq_client = None
GROQ_API_KEY = get_api_key("GROQ_API_KEY", config.GROQ_API_KEY)

if config.USE_GROQ and GROQ_API_KEY:
    try:
        groq_client = groq.Client(api_key=GROQ_API_KEY)
        print("Successfully initialized Groq client")
    except Exception as e:
        print(f"Error initializing Groq client: {str(e)}")
        groq_client = None

def get_vectorstore():
    """
    Load the vector store from disk
    
    Returns:
        Chroma: The vector store
    """
    # Check if vector store exists
    db_path = os.path.abspath(config.VECTOR_DB_PATH)
    print(f"Looking for vector database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Vector database directory not found at {db_path}")
        raise FileNotFoundError("Vector database not found. Please process a PDF first.")
    
    # Load the embeddings
    try:
        # For vectorstore, we'll use OpenAI embeddings if available, otherwise fall back to HuggingFace
        OPENAI_API_KEY = get_api_key("OPENAI_API_KEY")
        if OPENAI_API_KEY:
            print("Loading vector store with OpenAI embeddings")
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY  # Set for OpenAI libraries
            embeddings = OpenAIEmbeddings()
        else:
            print("Loading vector store with Hugging Face embeddings")
            embeddings = HuggingFaceEmbeddings(model_name=config.FALLBACK_MODEL)
    except Exception as e:
        print(f"Error loading embeddings: {str(e)}")
        print("Falling back to Hugging Face embeddings")
        embeddings = HuggingFaceEmbeddings(model_name=config.FALLBACK_MODEL)
    
    # Load the vector store
    try:
        print(f"Attempting to load Chroma DB from {db_path}")
        vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
        print("Vector store successfully loaded")
        return vectorstore
    except Exception as e:
        print(f"ERROR loading vector store: {str(e)}")
        traceback.print_exc()
        raise

def format_college_response(query, answer):
    """
    Format the response to make it more helpful for college-related questions
    
    Args:
        query (str): The user's query
        answer (str): The raw answer from the model
        
    Returns:
        str: Formatted answer
    """
    # If the answer is very short or seems unhelpful
    if len(answer.strip()) < 20 or "do not have" in answer.lower():
        return (
            f"Based on the college information provided in the PDF, I cannot find specific "
            f"details about '{query}'. This might be because:\n\n"
            f"1. This information is not included in the PDF you uploaded\n"
            f"2. The question needs to be more specific\n\n"
            f"You may want to check the college's official website or contact their "
            f"admissions office for more information about this topic."
        )
    
    return answer

def get_groq_completion(prompt, context, model=config.DEFAULT_MODEL):
    """
    Get a completion from Groq API directly
    
    Args:
        prompt (str): The prompt to send to the model
        context (str): The context to provide to the model
        model (str): The model to use
        
    Returns:
        str: The completion
    """
    if not groq_client:
        raise ValueError("Groq client not initialized")
    
    try:
        # Prepare the full prompt with context
        full_prompt = f"""You are a helpful college admissions assistant. Answer the following question based ONLY on the provided context from the college PDF.
Be concise but informative, and highlight key information that would be helpful for prospective students.

Context: {context}

Question: {prompt}

Helpful Answer:"""
        
        # Create a chat completion
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful college admissions assistant. Answer questions based ONLY on the provided context."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            model=model,
            temperature=0.2,
            max_tokens=1024,
        )
        
        # Extract the response
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error getting Groq completion: {str(e)}")
        traceback.print_exc()
        return f"Error getting response from Groq: {str(e)}"

def get_response(query, chat_history=[]):
    """
    Get a response to a query
    
    Args:
        query (str): The query to respond to
        chat_history (list): Chat history
        
    Returns:
        str: The response
    """
    try:
        # Get vector store
        vectorstore = get_vectorstore()
        
        # Create retriever with more documents for better context
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
        # Get relevant documents
        docs = retriever.get_relevant_documents(query)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # If using Groq and client is initialized, use direct API
        if config.USE_GROQ and groq_client:
            print(f"Using Groq model {config.DEFAULT_MODEL} directly")
            response = get_groq_completion(query, context)
            return format_college_response(query, response)
            
        # Otherwise use langchain
        # Create language model based on configuration
        if os.getenv("OPENAI_API_KEY"):
            print("Using OpenAI model for response generation")
            llm = ChatOpenAI(temperature=0.2)
            
            system_message = "You are a helpful college admissions assistant. Answer questions based ONLY on the provided context."
        else:
            # Fall back to Hugging Face model
            print("Using Hugging Face model for response generation")
            llm = HuggingFaceHub(
                repo_id="google/flan-t5-large",
                model_kwargs={"temperature": 0.5, "max_length": 512}
            )
            
            system_message = None
        
        # Create template for all models
        template = (
            "You are a helpful assistant for a college. "
            "Use the following pieces of context to answer the question. "
            "If you don't know the answer, say that you don't know and suggest contacting the college directly. "
            "Keep answers concise and accurate, focusing only on information from the provided context.\n\n"
            "Context: {context}\n"
            "Question: {question}\n"
            "Helpful Answer:"
        )
        
        # Create conversation chain with memory
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            return_source_documents=True,
            verbose=True
        )
        
        # Get response
        result = qa_chain({"question": query, "chat_history": chat_history})
        
        # Format the response
        return format_college_response(query, result["answer"])
    except Exception as e:
        error_msg = str(e)
        print(f"Error generating response: {error_msg}")
        traceback.print_exc()
        
        if "Vector database not found" in error_msg:
            return "You need to upload and process a PDF document first. Please use the sidebar to upload your college PDF."
        else:
            return (
                f"I'm sorry, I encountered an error: {error_msg}. "
                f"Please make sure you have uploaded and processed a PDF, "
                f"and that you have set up your environment correctly."
            ) 