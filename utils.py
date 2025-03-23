import re
import os
import string
import unicodedata
import logging
from typing import Dict, List, Any, Tuple, Set
import json
import random

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google News API key from environment variable
GOOGLE_NEWS_API_KEY = os.getenv("GOOGLE_NEWS_API_KEY", "AIzaSyBtsAyxYHzO6I1oCNBlftDrGIuBrjxhJt4")

def sanitize_company_name(company_name: str) -> str:
    """
    Sanitize company name by removing special characters and extra spaces.
    
    Args:
        company_name: The company name to sanitize
        
    Returns:
        Sanitized company name
    """
    if not company_name:
        return ""
    
    # Remove accents and convert to ASCII
    company_name = unicodedata.normalize('NFKD', company_name)
    company_name = ''.join([c for c in company_name if not unicodedata.combining(c)])
    
    # Remove special characters but keep alphanumerics and spaces
    company_name = re.sub(r'[^\w\s]', '', company_name)
    
    # Replace multiple spaces with a single space and trim
    company_name = re.sub(r'\s+', ' ', company_name).strip()
    
    return company_name

def extract_topics(text: str, existing_topics: Set[str] = None) -> List[str]:
    """
    Extract topics from article text.
    
    Args:
        text: The article text to extract topics from
        existing_topics: Set of topics already extracted
        
    Returns:
        List of topics
    """
    # This is a simple implementation that could be improved with NLP techniques
    # We're just using common business and tech keywords for now
    business_tech_keywords = {
        "Finance": ["finance", "financial", "stock", "investment", "investor", "profit", "revenue", "earnings", "market", "economy"],
        "Technology": ["technology", "tech", "digital", "software", "hardware", "app", "application", "innovation", "AI", "artificial intelligence", "machine learning"],
        "Regulation": ["regulation", "regulatory", "compliance", "law", "legal", "legislation", "policy", "government"],
        "Expansion": ["growth", "expand", "expansion", "global", "international", "market", "new markets", "strategy"],
        "Products": ["product", "launch", "release", "new", "feature", "service", "solution"],
        "Management": ["CEO", "executive", "leadership", "management", "board", "director", "chairman"],
        "Industry": ["industry", "sector", "competition", "competitor", "market share"],
        "Innovation": ["innovation", "R&D", "research", "development", "patent", "breakthrough", "disruptive"]
    }
    
    if existing_topics is None:
        existing_topics = set()
    
    found_topics = set()
    text_lower = text.lower()
    
    for topic, keywords in business_tech_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text_lower and topic not in existing_topics:
                found_topics.add(topic)
                break
    
    # Ensure we have at least one topic, add a relevant one if none found
    if not found_topics and not existing_topics:
        found_topics.add("Business News")
    
    return list(found_topics)

def extract_text_fragments(full_text: str, max_fragments: int = 3, min_length: int = 50, max_length: int = 150) -> List[str]:
    """
    Extract text fragments from the full text of an article.
    
    Args:
        full_text: The full text of the article
        max_fragments: Maximum number of fragments to extract
        min_length: Minimum length of each fragment
        max_length: Maximum length of each fragment
        
    Returns:
        List of text fragments
    """
    if not full_text:
        return []
    
    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) >= min_length]
    
    fragments = []
    current_fragment = ""
    
    for sentence in sentences:
        if len(current_fragment) + len(sentence) <= max_length:
            current_fragment += " " + sentence if current_fragment else sentence
        else:
            if current_fragment:
                fragments.append(current_fragment)
                current_fragment = sentence
                
                if len(fragments) >= max_fragments:
                    break
    
    # Add the last fragment if it exists and we haven't reached max_fragments
    if current_fragment and len(fragments) < max_fragments:
        fragments.append(current_fragment)
    
    # If we still don't have enough fragments and have more sentences
    remaining_sentences = len(fragments)
    if remaining_sentences < max_fragments and remaining_sentences < len(sentences):
        additional_sentences = sentences[remaining_sentences:remaining_sentences + (max_fragments - remaining_sentences)]
        for sentence in additional_sentences:
            if len(sentence) <= max_length:
                fragments.append(sentence)
            else:
                fragments.append(sentence[:max_length] + "...")
    
    return fragments

def calculate_topic_overlap(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate topic overlap across articles.
    
    Args:
        articles: List of articles with topics
        
    Returns:
        Dictionary with topic overlap analysis
    """
    # Extract topics from all articles
    article_topics = []
    all_topics = set()
    
    for article in articles:
        topics = set(article.get("Topics", []))
        article_topics.append(topics)
        all_topics.update(topics)
    
    # Calculate common topics (present in more than one article)
    topic_counts = {topic: 0 for topic in all_topics}
    for topics in article_topics:
        for topic in topics:
            topic_counts[topic] += 1
    
    common_topics = [topic for topic, count in topic_counts.items() if count > 1]
    
    # Calculate unique topics for each article
    unique_topics = {}
    for i, topics in enumerate(article_topics):
        unique_to_article = topics - set(common_topics)
        if unique_to_article:
            unique_topics[f"Unique Topics in Article {i+1}"] = list(unique_to_article)
    
    return {
        "Common Topics": common_topics if common_topics else ["None"],
        **unique_topics
    }

def generate_coverage_differences(articles: List[Dict[str, Any]], max_comparisons: int = 3) -> List[Dict[str, str]]:
    """
    Generate coverage differences between articles.
    
    Args:
        articles: List of articles
        max_comparisons: Maximum number of comparisons to generate
        
    Returns:
        List of dictionaries with comparison and impact
    """
    if len(articles) < 2:
        return []
    
    # Select a subset of articles for comparison
    num_articles = min(len(articles), 5)  # Limit to 5 articles for comparison
    article_indices = list(range(num_articles))
    
    comparisons = []
    for _ in range(min(max_comparisons, num_articles*(num_articles-1)//2)):
        if not article_indices or len(article_indices) < 2:
            break
            
        # Select two different articles
        idx1, idx2 = random.sample(article_indices, 2)
        article1 = articles[idx1]
        article2 = articles[idx2]
        
        # Compare sentiment
        sentiment1 = article1.get("Sentiment", "Neutral")
        sentiment2 = article2.get("Sentiment", "Neutral")
        
        # Compare topics
        topics1 = set(article1.get("Topics", []))
        topics2 = set(article2.get("Topics", []))
        
        common_topics = topics1.intersection(topics2)
        unique_topics1 = topics1 - topics2
        unique_topics2 = topics2 - topics1
        
        # Generate comparison text
        if sentiment1 != sentiment2:
            comparison = f"Article {idx1+1} has a {sentiment1.lower()} sentiment, while Article {idx2+1} has a {sentiment2.lower()} sentiment."
        elif unique_topics1 and unique_topics2:
            comparison = f"Article {idx1+1} focuses on {', '.join(unique_topics1)}, while Article {idx2+1} focuses on {', '.join(unique_topics2)}."
        elif unique_topics1:
            comparison = f"Article {idx1+1} covers {', '.join(unique_topics1)}, which is not mentioned in Article {idx2+1}."
        elif unique_topics2:
            comparison = f"Article {idx2+1} covers {', '.join(unique_topics2)}, which is not mentioned in Article {idx1+1}."
        else:
            comparison = f"Article {idx1+1} and Article {idx2+1} cover similar topics with {sentiment1.lower()} sentiment."
        
        # Generate impact text
        if sentiment1 != sentiment2:
            if sentiment1 == "Positive" and sentiment2 == "Negative":
                impact = f"This contrast could indicate mixed market signals or different perspectives on the company's performance."
            elif sentiment1 == "Negative" and sentiment2 == "Positive":
                impact = f"The contradicting sentiments suggest complex developments that may be interpreted differently by various sources."
            else:
                impact = f"The difference in sentiment reflects varying assessments of the company's situation."
        elif unique_topics1 and unique_topics2:
            impact = f"These different focus areas provide a more comprehensive view of the company's operations and challenges."
        else:
            impact = f"The articles reinforce each other's perspective, adding credibility to the {sentiment1.lower()} outlook."
        
        comparisons.append({
            "Comparison": comparison,
            "Impact": impact
        })
        
    return comparisons
