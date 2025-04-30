# UniBot - College Information Chatbot

A simple chatbot application that can answer questions about your college based on PDF documents. This application automatically processes PDF files from the `docs` directory and creates a chat interface for asking questions about B.Tech and M.Tech programs.

## Features

- Automatically loads and processes PDF documents from the `docs` directory
- Chat-based interface for asking questions
- Context-aware responses based on the PDF content
- Multiple PDF extraction methods for better compatibility
- Support for both Groq and OpenAI APIs, with fallback to local models

## Requirements

- Python 3.8 or higher
- Required packages (see `requirements.txt`)

## Setup

1. Clone this repository:
```
git clone <repository-url>
cd unibot
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. (Optional) Set up API keys:
   
   Create a `.env` file in the project root and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
   ```
   
   The application uses Groq API by default (configured in `config.py`), but can fall back to local models if needed.

4. Place your PDF files in the `docs` directory. The default configuration looks for:
   - `BTech_MTech_2022.pdf` (primary)
   - `student-handbook-2018-2019-jain-university.pdf` (fallback)
   - `Jain Shaata.pdf` (fallback)

## Usage

1. Run the application:
```
streamlit run app.py
```

2. Open your web browser and go to the URL displayed in the terminal (usually http://localhost:8501)

3. The application will automatically process PDF files from the `docs` directory

4. Ask questions in the chat interface!

## How it Works

1. **PDF Processing**: The application automatically extracts text from PDF files in the `docs` directory.

2. **Text Chunking**: The extracted text is split into smaller chunks for processing.

3. **Vector Database**: These chunks are converted into vector embeddings and stored in a database.

4. **Question Answering**: When you ask a question, the application finds the most relevant chunks of text and uses them to generate a response.

## Files in this Project

- `app.py`: Main application file with Streamlit UI
- `pdf_processor.py`: Handles PDF text extraction and vector database creation
- `chatbot.py`: Processes queries and generates responses
- `config.py`: Contains configuration settings
- `requirements.txt`: List of required Python packages
- `docs/`: Directory containing PDF files to be processed

## Customization

You can customize the behavior of the chatbot by modifying the settings in `config.py`.

## Troubleshooting

If you encounter issues:

1. Make sure you have uploaded and processed a PDF
2. Check that you have installed all required dependencies
3. If using OpenAI, verify that your API key is correct
4. Try using a different PDF if the current one is not being processed correctly

## License

This project is licensed under the MIT License - see the LICENSE file for details.