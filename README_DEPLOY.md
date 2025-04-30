# Deploying UniBot to Streamlit Cloud

This document provides instructions for deploying UniBot to Streamlit Cloud.

## Prerequisites

1. A GitHub account
2. A Streamlit Cloud account (free tier is sufficient)
3. Your API keys (Groq, OpenAI, or Hugging Face)

## Deployment Steps

### 1. Prepare the Repository

1. Push your code to a GitHub repository:
   ```bash
   git add .
   git commit -m "Prepare for Streamlit deployment"
   git push
   ```

2. Make sure your repository contains the following files:
   - `requirements.txt`
   - `app.py`
   - `.streamlit/config.toml`
   - `.streamlit/secrets.toml`

### 2. Set Up Streamlit Cloud

1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Sign in with your GitHub account
3. Click on "New app"
4. Select your GitHub repository, branch, and the main file (`app.py`)
5. Click "Deploy"

### 3. Configure Secrets

1. Once the app is deployed, go to "App settings" in the Streamlit Cloud dashboard
2. Navigate to the "Secrets" section
3. Add your API keys in the following format:
   ```toml
   GROQ_API_KEY = "your-groq-api-key"
   OPENAI_API_KEY = "your-openai-api-key"
   HUGGINGFACEHUB_API_TOKEN = "your-huggingface-token"
   ```
4. Click "Save"

### 4. Advanced Configuration (Optional)

1. You can customize app settings such as theme, memory, and timeout in the Streamlit Cloud dashboard
2. For better performance, consider increasing the memory allocation

## Troubleshooting

If you encounter issues with the ChromaDB:

1. Check that the app is creating the database in the `/tmp/chroma_db` directory
2. Verify that the necessary Python packages are included in `requirements.txt`
3. Ensure API keys are properly set in the Streamlit Cloud secrets

## Local Testing of Deployment

To test the app locally as it would run in Streamlit Cloud:

```bash
export STREAMLIT_SHARING=true
streamlit run app.py
```

This will simulate the Streamlit Cloud environment by using the temporary storage for ChromaDB.

## Limitations

- The vector database will be recreated on each app restart in Streamlit Cloud
- There may be memory constraints in the free tier that limit the size of PDFs you can process
- Cold starts may take a few seconds when the app hasn't been used for a while 