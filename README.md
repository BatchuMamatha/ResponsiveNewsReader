
# News Summarization & Sentiment Analysis App

A web application that extracts news articles about companies, performs sentiment analysis, and generates Hindi text-to-speech summaries.

## Features

- Company news extraction from multiple sources
- Sentiment analysis of news articles
- Topic extraction and categorization
- Hindi text-to-speech summary generation
- Interactive web interface using Streamlit
- RESTful API backend using FastAPI

## Components

- **Frontend** (`app.py`): Streamlit web interface
- **Backend** (`api.py`): FastAPI server for news processing
- **News Scraper** (`news_scraper.py`): News article extraction
- **Sentiment Analyzer** (`sentiment_analyzer.py`): News sentiment analysis
- **TTS Generator** (`tts_generator.py`): Hindi text-to-speech conversion
- **Utils** (`utils.py`): Helper functions

## Running the Application

1. The frontend runs on port 5000: Access via the "Run" button
2. The backend API runs on port 8000: Start with the "News Analyzer Backend API" workflow

## Technology Stack

- Python
- Streamlit (Frontend)
- FastAPI (Backend)
- NLTK (Natural Language Processing)
- gTTS (Google Text-to-Speech)
- BeautifulSoup (Web Scraping)
- Trafilatura (Content Extraction)


## Demo Video  

🎥 [Click here to watch the video](https://drive.google.com/file/d/1MdjtyC7n_zZ0cfhv-Zk0Qm1CDhUSXz1f/view?usp=sharing)
