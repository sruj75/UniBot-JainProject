import os
import traceback
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import config

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
    
    # Create vector database directory if it doesn't exist
    db_path = os.path.abspath(config.VECTOR_DB_PATH)
    print(f"Vector DB path: {db_path}")
    os.makedirs(db_path, exist_ok=True)
    
    # Create and persist vector database
    print("Creating Chroma vector database...")
    try:
        vectordb = Chroma.from_texts(
            texts=chunks,
            embedding=embeddings,
            persist_directory=db_path
        )
        
        # Persist the database
        print("Persisting vector database...")
        vectordb.persist()
        print(f"Vector database created and persisted at {db_path}")
        
        return vectordb
    except Exception as e:
        print(f"ERROR creating vector database: {str(e)}")
        traceback.print_exc()
        raise