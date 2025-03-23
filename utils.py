import requests
from bs4 import BeautifulSoup
import trafilatura
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import re
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    logger.warning(f"Error downloading NLTK resources: {str(e)}")

def clean_text(text):
    """Clean text by removing special characters, extra spaces, etc."""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    return text.strip()

def summarize_text(text, max_sentences=5):
    """
    Extractive summarization - selects the most important sentences from the text
    """
    if not text:
        return "No content available to summarize."
        
    # Clean the text
    text = clean_text(text)
    
    # Tokenize into sentences
    sentences = sent_tokenize(text)
    
    # If text is short enough, return as is
    if len(sentences) <= max_sentences:
        return text
        
    # For simple extractive summarization, just take first few sentences
    # In a real application, you would use a more sophisticated approach
    summary = ' '.join(sentences[:max_sentences])
    
    return summary

def fetch_url_content(url):
    """Fetch content from a URL using requests and BeautifulSoup"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Use trafilatura if available, otherwise use BeautifulSoup
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        
        if not text:
            # Fallback to BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            
        return clean_text(text)
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {str(e)}")
        return None

def get_api_key(env_var, default=None):
    """Safely get API key from environment variables with fallback"""
    return os.getenv(env_var, default)

def chunk_text(text, max_chunk_size=4500):
    """Split text into chunks for API processing"""
    chunks = []
    sentences = sent_tokenize(text)
    
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def calculate_word_frequency(texts):
    """Calculate word frequency across multiple texts"""
    stop_words = set(stopwords.words('english'))
    word_freq = {}
    
    for text in texts:
        if not text:
            continue
            
        # Tokenize and lowercase
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Count words (excluding stop words)
        for word in words:
            if word not in stop_words and len(word) > 2:
                if word in word_freq:
                    word_freq[word] += 1
                else:
                    word_freq[word] = 1
    
    return word_freq
