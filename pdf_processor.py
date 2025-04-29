import os
import traceback
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import config

def process_pdf(pdf_path):
    """
    Extract text from a PDF file
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    # Check if file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        # Primary method: Extract text from PDF using PyPDF
        text = extract_with_pypdf(pdf_path)
        
        # If text extraction failed or got minimal text, try alternate method
        if not text or len(text.strip()) < 100:
            try:
                # Try to import and use PyMuPDF (fitz) as a fallback
                import fitz
                text = extract_with_pymupdf(pdf_path)
                print("Used PyMuPDF for text extraction")
            except ImportError:
                print("PyMuPDF not available, using PyPDF results")
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        traceback.print_exc()
        raise
    
    return text

def extract_with_pypdf(pdf_path):
    """
    Extract text using PyPDF
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    # Extract text from PDF
    reader = PdfReader(pdf_path)
    text = ""
    
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n\n"  # Add double newline between pages
    
    return text

def extract_with_pymupdf(pdf_path):
    """
    Extract text using PyMuPDF (fitz)
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    import fitz  # PyMuPDF
    
    doc = fitz.open(pdf_path)
    text = ""
    
    for page in doc:
        text += page.get_text() + "\n\n"  # Add double newline between pages
    
    return text

def create_vector_db(text):
    """
    Create a vector database from the extracted text
    
    Args:
        text (str): Extracted text from the PDF
    """
    # Check if text is empty
    if not text or len(text.strip()) == 0:
        raise ValueError("Extracted text is empty. Cannot create vector database.")
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    if not chunks:
        raise ValueError("No text chunks created. Text splitting failed.")
    
    print(f"Created {len(chunks)} text chunks for vectorization")
    
    # Create embeddings
    try:
        # Try to use OpenAI embeddings if API key is available
        if os.getenv("OPENAI_API_KEY"):
            print("Using OpenAI embeddings")
            embeddings = OpenAIEmbeddings()
        else:
            # Fall back to local embeddings model
            print("Using local Hugging Face embeddings")
            embeddings = HuggingFaceEmbeddings(model_name=config.FALLBACK_MODEL)
    except Exception as e:
        # Always fall back to local embeddings if there's an issue
        print(f"Using local embeddings due to: {str(e)}")
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
    
    return vectordb