# News Summarization and Text-to-Speech Application

This application extracts key details from multiple news articles related to a given company, performs sentiment analysis, conducts a comparative analysis, and generates a text-to-speech (TTS) output in Hindi.

## Features

- News extraction from multiple sources using BeautifulSoup
- Sentiment analysis of article content (positive/negative/neutral)
- Comparative sentiment analysis across all articles
- Topic extraction from article content
- Text-to-speech conversion to Hindi
- Simple and intuitive web interface using Streamlit

## Project Structure

- `app.py`: Streamlit web interface
- `api.py`: FastAPI backend for processing requests
- `utils.py`: Utility functions
- `news_scraper.py`: News article scraping functionality
- `sentiment_analyzer.py`: Sentiment analysis functionality
- `tts_service.py`: Text-to-speech functionality
- `.streamlit/config.toml`: Streamlit configuration

## Setup Instructions

1. **Clone the repository**

```bash
git clone <repository-url>
cd <repository-directory>
