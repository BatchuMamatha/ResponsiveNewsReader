import requests
import json
import time
from bs4 import BeautifulSoup
import trafilatura
import os
import re
import logging
import utils
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API key for Google News API
GOOGLE_API_KEY = utils.get_api_key("API_KEY", "AIzaSyBtsAyxYHzO6I1oCNBlftDrGIuBrjxhJt4")
SEARCH_ENGINE_ID = "YOUR_SEARCH_ENGINE_ID"  # Replace with your custom search engine ID (fallback)

def get_news_articles(company_name, max_results=15):
    """
    Get news articles about a specific company using a combination of methods
    to ensure we get enough articles.
    """
    logger.info(f"Fetching news for: {company_name}")
    
    # Try different methods to get news, starting with Google News
    articles = get_articles_from_google_news(company_name)
    
    # If we didn't get enough articles, try other sources
    if len(articles) < max_results:
        additional_articles = get_articles_from_news_sites(company_name)
        
        # Add new articles while avoiding duplicates
        for article in additional_articles:
            if article['url'] not in [a['url'] for a in articles]:
                articles.append(article)
                if len(articles) >= max_results:
                    break
    
    # Return only non-JS sites that can be scraped with BeautifulSoup
    scrapable_articles = []
    for article in articles:
        if is_scrapable_url(article['url']):
            scrapable_articles.append(article)
    
    logger.info(f"Found {len(scrapable_articles)} scrapable articles out of {len(articles)} total")
    return scrapable_articles[:max_results]

def get_articles_from_google_news(query, num_results=15):
    """
    Get news articles using Google Custom Search API
    """
    articles = []
    
    try:
        # Build the search query
        search_query = f"{query} news"
        
        # Make the API request
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': SEARCH_ENGINE_ID,
            'q': search_query,
            'num': num_results,
            'searchType': 'news'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            search_results = response.json()
            
            # Extract articles
            if 'items' in search_results:
                for item in search_results['items']:
                    article = {
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'source': item.get('displayLink', ''),
                        'snippet': item.get('snippet', '')
                    }
                    articles.append(article)
        else:
            logger.warning(f"Google API returned status code {response.status_code}: {response.text}")
            
    except Exception as e:
        logger.error(f"Error getting articles from Google News: {str(e)}")
    
    # If we couldn't get articles from the API, fallback to direct scraping
    if not articles:
        articles = get_articles_from_news_sites(query)
        
    return articles

def get_articles_from_news_sites(company_name):
    """
    Fallback method: Directly scrape news articles from common news sites.
    This is a backup in case the Google API doesn't work.
    """
    articles = []
    
    # List of news sites to scrape
    news_sites = [
        f"https://news.google.com/search?q={company_name}",
        f"https://www.reuters.com/search/news?blob={company_name}",
        f"https://economictimes.indiatimes.com/searchresult.cms?query={company_name}",
        f"https://www.business-standard.com/search?q={company_name}"
    ]
    
    for site in news_sites:
        try:
            response = requests.get(site, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract articles (basic scraping, each site needs custom rules)
                # This is a simplified example
                article_elements = soup.select('article') or soup.select('.article') or soup.select('.story')
                
                for element in article_elements[:5]:  # Limit to 5 from each source
                    title_elem = element.select_one('h3') or element.select_one('h2') or element.select_one('.title')
                    link_elem = element.select_one('a')
                    
                    if title_elem and link_elem and link_elem.get('href'):
                        url = link_elem['href']
                        if not url.startswith('http'):
                            # Convert relative URL to absolute
                            base_url = '/'.join(site.split('/')[:3])
                            url = f"{base_url}{url if url.startswith('/') else '/' + url}"
                            
                        article = {
                            'title': title_elem.text.strip(),
                            'url': url,
                            'source': site.split('/')[2],
                            'snippet': ''
                        }
                        articles.append(article)
        except Exception as e:
            logger.error(f"Error scraping {site}: {str(e)}")
    
    return articles

def is_scrapable_url(url):
    """
    Check if a URL is likely to be scrapable with BeautifulSoup (i.e., not a JS-heavy site)
    """
    # List of domains known to be difficult to scrape with BeautifulSoup
    difficult_domains = [
        'twitter.com', 
        'facebook.com', 
        'instagram.com',
        'youtube.com'
    ]
    
    for domain in difficult_domains:
        if domain in url:
            return False
    
    return True

def extract_article_content(url):
    """
    Extract the main content from a news article
    """
    try:
        # Try trafilatura first (usually better at extracting article content)
        downloaded = trafilatura.fetch_url(url)
        content = trafilatura.extract(downloaded)
        
        if not content or len(content) < 100:
            # Fallback to BeautifulSoup
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Look for article content in common elements
            article_content = soup.select_one('article') or soup.select_one('.article-content') or soup.select_one('.content')
            
            if article_content:
                content = article_content.get_text()
            else:
                # Fallback to get all text
                content = soup.get_text()
        
        # Clean and return the content
        return utils.clean_text(content)
        
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return None
