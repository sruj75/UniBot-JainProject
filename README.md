# College Information Chatbot

This is a simple chatbot application that can answer questions about your college based on a PDF document. It uses natural language processing and machine learning to understand questions and provide relevant answers.

## Features

- Upload and process PDF documents containing college information
- Chat-based interface for asking questions
- Context-aware responses based on the PDF content
- Support for both OpenAI and local models

## Requirements

- Python 3.8 or higher
- Required packages (see `requirements.txt`)

## Setup

1. Clone this repository:
```
git clone <repository-url>
cd college-chatbot
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. (Optional) Set up environment variables:
   
   Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   
   If you don't have an OpenAI API key, the application will fall back to using local models.

## Usage

1. Run the application:
```
streamlit run app.py
```

2. Open your web browser and go to the URL displayed in the terminal (usually http://localhost:8501)

3. Upload your college PDF document using the file uploader in the sidebar

4. Click the "Process PDF" button to extract information from the PDF

5. Ask questions in the chat interface! The chatbot will respond based on the content of your PDF

## How it Works

1. **PDF Processing**: The application extracts text from the uploaded PDF document.

2. **Text Chunking**: The extracted text is split into smaller chunks for processing.

3. **Vector Database**: These chunks are converted into vector embeddings and stored in a database.

4. **Question Answering**: When you ask a question, the application finds the most relevant chunks of text and uses them to generate a response.

## Customization

You can customize the behavior of the chatbot by modifying the following parameters:

- In `pdf_processor.py`:
  - `chunk_size`: The size of text chunks (default: 1000)
  - `chunk_overlap`: The overlap between chunks (default: 200)

- In `chatbot.py`:
  - `search_kwargs={"k": 3}`: The number of chunks to retrieve (default: 3)
  - `temperature`: Controls the randomness of responses (default: 0)

## Troubleshooting

If you encounter issues:

1. Make sure you have uploaded and processed a PDF
2. Check that you have installed all required dependencies
3. If using OpenAI, verify that your API key is correct
4. Try using a different PDF if the current one is not being processed correctly

## License

This project is licensed under the MIT License - see the LICENSE file for details.