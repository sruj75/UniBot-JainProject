import os
import traceback
from langchain.text_splitter import RecursiveCharacterTextSplitter
import config

# Try to import vector store libraries
try:
    from langchain_community.vectorstores import Chroma
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("Warning: ChromaDB not available")

# Try to import FAISS as an alternative to Chroma
try:
    from langchain_community.vectorstores import FAISS
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available")

# Try SQLite version check
import sqlite3
SQLITE_VERSION = sqlite3.sqlite_version_info
SQLITE_COMPATIBLE = SQLITE_VERSION >= (3, 35, 0)
if not SQLITE_COMPATIBLE:
    print(f"SQLite version {sqlite3.sqlite_version} is below 3.35.0, which is required for ChromaDB")

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

# Try to import PDF libraries, but don't fail if not available
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("Warning: pypdf not available, PDF processing will be limited")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available, PDF processing will be limited")

# This will be our fallback when ChromaDB/FAISS are not available
from langchain_community.vectorstores import DocArrayInMemorySearch

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
        if PYPDF_AVAILABLE:
            text = extract_with_pypdf(pdf_path)
            
            # If text extraction failed or got minimal text, try alternate method
            if not text or len(text.strip()) < 100:
                if PYMUPDF_AVAILABLE:
                    text = extract_with_pymupdf(pdf_path)
                    print("Used PyMuPDF for text extraction")
        elif PYMUPDF_AVAILABLE:
            text = extract_with_pymupdf(pdf_path)
            print("Used PyMuPDF for text extraction")
        else:
            print("No PDF extraction libraries available")
            text = ""
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        traceback.print_exc()
        text = ""
    
    return text

def extract_with_pypdf(pdf_path):
    """
    Extract text from a PDF file using pypdf
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    if not PYPDF_AVAILABLE:
        return ""
        
    try:
        pdf = PdfReader(pdf_path)
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting with PyPDF: {str(e)}")
        return ""

def extract_with_pymupdf(pdf_path):
    """
    Extract text from a PDF file using PyMuPDF
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    if not PYMUPDF_AVAILABLE:
        return ""
        
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting with PyMuPDF: {str(e)}")
        return ""

def create_vector_db(text=None):
    """
    Create a vector database from the extracted text or use fallback text
    
    Args:
        text (str): Extracted text from the PDF. If None, uses fallback text
    """
    print("Starting vector database creation")
    
    # Use sample text if no valid text is provided
    if not text or len(text.strip()) < 100:
        print("Using default sample text since provided text is too short or empty")
        # Use a sample text about the college to create a basic vector database
        text = """
# Jain University B.Tech and M.Tech Programs Information

## B.Tech Programs

### Admission Requirements
- Minimum 60% aggregate in 10+2 or equivalent with Physics, Chemistry, and Mathematics
- Valid JEE Main/KCET/COMEDK score
- Direct admission based on merit for top performers

### Available Specializations
1. Computer Science Engineering
2. Information Technology
3. Electronics and Communication Engineering
4. Mechanical Engineering
5. Civil Engineering
6. Electrical and Electronics Engineering
7. Artificial Intelligence and Machine Learning
8. Data Science

### Fee Structure
- Tuition Fee: Rs. 180,000 per year
- Hostel Fee: Rs. 120,000 per year (optional)
- One-time admission fee: Rs. 25,000
- Scholarships available for meritorious students

## M.Tech Programs
### Admission Requirements
- B.Tech/B.E. with minimum 60% aggregate
- Valid GATE score preferred (not mandatory)
- Selection based on entrance test and interview

### Available Specializations
1. Computer Science Engineering
2. Digital Communication
3. Power Electronics
4. Structural Engineering
5. Machine Design
6. Data Science and AI
"""
    
    # Split text into chunks
    print(f"Text length: {len(text)} characters")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    if not chunks:
        print("ERROR: No text chunks created")
        raise ValueError("No text chunks created. Text splitting failed.")
    
    print(f"Created {len(chunks)} text chunks for vectorization")
    
    # Create embeddings - ALWAYS use HuggingFace for simplicity and reliability
    print("Using local Hugging Face embeddings")
    try:
        embeddings = HuggingFaceEmbeddings(model_name=config.FALLBACK_MODEL)
    except Exception as e:
        print(f"Error initializing embeddings: {str(e)}")
        traceback.print_exc()
        raise
    
    # Decision tree for vector store selection
    # 1. Try ChromaDB if SQLite version is compatible
    # 2. Try FAISS if available
    # 3. Fall back to in-memory DocArray
    vectordb = None
    
    # If in Streamlit Cloud, mark this in the configuration
    is_streamlit_cloud = config.IS_STREAMLIT_CLOUD
    print(f"Running in Streamlit Cloud: {is_streamlit_cloud}")
    
    try:
        # First try Chroma if SQLite is compatible
        if CHROMA_AVAILABLE and SQLITE_COMPATIBLE:
            print("Trying ChromaDB vector database...")
            # Create vector database directory if it doesn't exist
            db_path = os.path.abspath(config.VECTOR_DB_PATH)
            print(f"Vector DB path: {db_path}")
            os.makedirs(db_path, exist_ok=True)
            
            vectordb = Chroma.from_texts(
                texts=chunks,
                embedding=embeddings,
                persist_directory=db_path
            )
            
            # Persist the database
            print("Persisting vector database...")
            vectordb.persist()
            print(f"ChromaDB vector database created and persisted at {db_path}")
        # Next try FAISS
        elif FAISS_AVAILABLE:
            print("Using FAISS vector database (ChromaDB not available or SQLite incompatible)")
            vectordb = FAISS.from_texts(chunks, embeddings)
            
            # Save FAISS index to disk
            faiss_path = os.path.join(config.VECTOR_DB_PATH, "faiss_index")
            os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
            vectordb.save_local(faiss_path)
            print(f"FAISS vector database created and saved at {faiss_path}")
        # Last resort: in-memory DocArray
        else:
            print("Using in-memory DocArrayInMemorySearch (ChromaDB and FAISS not available)")
            vectordb = DocArrayInMemorySearch.from_texts(chunks, embeddings)
            print("In-memory vector database created (will not persist)")
            
            # Set a global flag to indicate we're using an in-memory store
            config.USING_IN_MEMORY_DB = True
            
        return vectordb
    except Exception as e:
        print(f"ERROR creating vector database: {str(e)}")
        traceback.print_exc()
        
        # Last-resort fallback: create a minimal in-memory database regardless of error
        print("FALLBACK: Creating minimal in-memory vector database after error")
        config.USING_IN_MEMORY_DB = True
        return DocArrayInMemorySearch.from_texts(chunks, embeddings)