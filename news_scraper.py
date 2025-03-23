import requests
import bs4
from bs4 import BeautifulSoup
import logging
import trafilatura
import random
import time
from typing import List, Dict, Any
import urllib.parse
import os
import json
from utils import extract_topics, extract_text_fragments

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google News API key
GOOGLE_NEWS_API_KEY = os.getenv("GOOGLE_NEWS_API_KEY", "AIzaSyBtsAyxYHzO6I1oCNBlftDrGIuBrjxhJt4")

def get_google_news_urls(company_name: str, max_results: int = 15) -> List[str]:
    """
    Get news article URLs from Google News API.
    
    Args:
        company_name: The company name to search for
        max_results: Maximum number of results to return
        
    Returns:
        List of news article URLs
    """
    try:
        base_url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            "key": GOOGLE_NEWS_API_KEY,
            "cx": "017576662512468239146:omuauf_lfve",  # Custom Search Engine ID for news
            "q": f"{company_name} news",
            "num": max_results
        }
        
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        search_results = response.json()
        
        # Extract URLs from search results
        urls = []
        if "items" in search_results:
            for item in search_results["items"]:
                if "link" in item:
                    urls.append(item["link"])
        
        logger.info(f"Found {len(urls)} news URLs from Google News")
        return urls
    
    except Exception as e:
        logger.error(f"Error fetching news URLs from Google: {str(e)}")
        # Fallback to searching with DuckDuckGo if Google fails
        return get_fallback_news_urls(company_name, max_results)

def get_fallback_news_urls(company_name: str, max_results: int = 15) -> List[str]:
    """
    Fallback method to get news URLs if Google News API fails.
    Uses direct scraping of news sites.
    
    Args:
        company_name: The company name to search for
        max_results: Maximum number of results to return
        
    Returns:
        List of news article URLs
    """
    try:
        # List of news domains to check
        news_domains = [
            "reuters.com",
            "bloomberg.com",
            "cnbc.com",
            "wsj.com",
            "nytimes.com",
            "forbes.com",
            "businessinsider.com",
            "ft.com",
            "marketwatch.com",
            "techcrunch.com"
        ]
        
        all_urls = []
        
        # Try to search each domain
        for domain in news_domains:
            try:
                search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(company_name)}+site:{domain}"
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                response = requests.get(search_url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result links
                results = soup.select('.result__a')
                
                for result in results[:3]:  # Take up to 3 results per domain
                    href = result.get('href', '')
                    if href and domain in href:
                        # Extract the actual URL from DuckDuckGo redirect
                        actual_url = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get('uddg', [None])[0]
                        if actual_url and actual_url not in all_urls:
                            all_urls.append(actual_url)
                
                # Add some delay to avoid being blocked
                time.sleep(1)
                
                if len(all_urls) >= max_results:
                    break
                    
            except Exception as e:
                logger.warning(f"Error searching {domain}: {str(e)}")
                continue
        
        logger.info(f"Found {len(all_urls)} news URLs from fallback method")
        return all_urls[:max_results]
    
    except Exception as e:
        logger.error(f"Error in fallback news URL fetching: {str(e)}")
        return []

def scrape_news_article(url: str) -> Dict[str, Any]:
    """
    Scrape a news article from a given URL.
    
    Args:
        url: The URL of the news article
        
    Returns:
        Dictionary with article title, summary, and full text
    """
    try:
        # Add random delay to avoid being blocked
        time.sleep(random.uniform(1, 3))
        
        # Use trafilatura to extract clean text content
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            logger.warning(f"Failed to download content from {url}")
            return None
        
        # Extract main content
        extracted = trafilatura.extract(downloaded, output_format='xml', include_comments=False)
        
        if not extracted:
            logger.warning(f"Failed to extract content from {url}")
            return None
        
        # Parse the XML output
        soup = BeautifulSoup(extracted, 'xml')
        
        # Extract title
        title = soup.find('title')
        title_text = title.text.strip() if title else "No title found"
        
        # Extract full text
        full_text = ""
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            full_text += p.text.strip() + " "
        
        # Generate summary and extract topics
        topics = extract_topics(full_text)
        
        # Generate a summary by extracting key fragments
        summary_fragments = extract_text_fragments(full_text)
        summary = " ".join(summary_fragments) if summary_fragments else "No summary available"
        
        return {
            "Title": title_text,
            "Summary": summary,
            "URL": url,
            "Topics": topics
        }
    
    except Exception as e:
        logger.error(f"Error scraping article from {url}: {str(e)}")
        return None

def get_news_articles(company_name: str, min_articles: int = 10) -> List[Dict[str, Any]]:
    """
    Get news articles for a given company.
    
    Args:
        company_name: The company name to search for
        min_articles: Minimum number of articles to retrieve
        
    Returns:
        List of articles with title, summary, URL, and topics
    """
    try:
        # Get URLs of news articles
        urls = get_google_news_urls(company_name)
        
        if not urls or len(urls) == 0:
            logger.warning(f"No news URLs found for {company_name}")
            return []
        
        articles = []
        
        # Try to scrape articles until we have enough
        for url in urls:
            article = scrape_news_article(url)
            
            if article:
                articles.append(article)
                logger.info(f"Successfully scraped article: {article['Title']}")
            
            if len(articles) >= min_articles:
                break
        
        # If we don't have enough articles, try the fallback method
        if len(articles) < min_articles:
            logger.info(f"Only found {len(articles)} articles, trying fallback method")
            fallback_urls = get_fallback_news_urls(company_name)
            
            for url in fallback_urls:
                if url not in urls:  # Avoid duplicates
                    article = scrape_news_article(url)
                    
                    if article:
                        articles.append(article)
                        logger.info(f"Successfully scraped article (fallback): {article['Title']}")
                    
                    if len(articles) >= min_articles:
                        break
        
        logger.info(f"Total articles found for {company_name}: {len(articles)}")
        return articles
    
    except Exception as e:
        logger.error(f"Error getting news articles for {company_name}: {str(e)}")
        return []
