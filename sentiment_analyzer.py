import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import logging
import os
import json
from typing import Dict, List, Any, Tuple
from utils import calculate_topic_overlap, generate_coverage_differences

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('vader_lexicon')

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze sentiment of a given text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary with sentiment category and sentiment scores
    """
    try:
        if not text:
            return {"Sentiment": "Neutral", "Scores": {"pos": 0, "neg": 0, "neu": 1, "compound": 0}}
        
        # Get sentiment scores
        sentiment = sia.polarity_scores(text)
        
        # Determine sentiment category
        compound_score = sentiment['compound']
        
        if compound_score >= 0.05:
            sentiment_category = "Positive"
        elif compound_score <= -0.05:
            sentiment_category = "Negative"
        else:
            sentiment_category = "Neutral"
        
        return {"Sentiment": sentiment_category, "Scores": sentiment}
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        return {"Sentiment": "Neutral", "Scores": {"pos": 0, "neg": 0, "neu": 1, "compound": 0}}

def generate_comparative_analysis(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comparative analysis across multiple articles.
    
    Args:
        articles: List of articles with sentiment analysis
        
    Returns:
        Dictionary with comparative analysis
    """
    try:
        if not articles:
            return {
                "Sentiment Distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
                "Coverage Differences": [],
                "Topic Overlap": {"Common Topics": [], "Unique Topics": []}
            }
        
        # Count sentiment distribution
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        
        for article in articles:
            sentiment = article.get("Sentiment", "Neutral")
            sentiment_counts[sentiment] += 1
        
        # Calculate topic overlap
        topic_overlap = calculate_topic_overlap(articles)
        
        # Generate coverage differences
        coverage_differences = generate_coverage_differences(articles)
        
        return {
            "Sentiment Distribution": sentiment_counts,
            "Coverage Differences": coverage_differences,
            "Topic Overlap": topic_overlap
        }
    
    except Exception as e:
        logger.error(f"Error generating comparative analysis: {str(e)}")
        return {
            "Sentiment Distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
            "Coverage Differences": [],
            "Topic Overlap": {"Common Topics": [], "Unique Topics": []}
        }
