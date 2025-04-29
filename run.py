#!/usr/bin/env python3
import os
import subprocess
import sys

def check_requirements():
    """Check if all requirements are installed."""
    try:
        import streamlit
        import pypdf
        import langchain
        import langchain_openai
        import langchain_community
        import dotenv
        import chromadb
        return True
    except ImportError as e:
        print(f"Missing requirement: {e}")
        return False

def install_requirements():
    """Install requirements from requirements.txt."""
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def main():
    """Main function to run the application."""
    # Check if requirements are installed
    if not check_requirements():
        print("Some requirements are missing.")
        response = input("Do you want to install them? (y/n): ")
        if response.lower() == 'y':
            install_requirements()
        else:
            print("Please install the requirements manually and try again.")
            sys.exit(1)
    
    # Run the Streamlit app
    print("Starting the application...")
    subprocess.call(["streamlit", "run", "app.py"])

if __name__ == "__main__":
    main() 