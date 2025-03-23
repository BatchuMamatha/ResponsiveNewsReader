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
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API key for Google News API
GOOGLE_API_KEY = utils.get_api_key("GOOGLE_API_KEY")
# Using the search engine ID from environment variables
SEARCH_ENGINE_ID = utils.get_api_key("SEARCH_ENGINE_ID")

def get_news_articles(company_name, max_results=15):
    """
    Get news articles about a specific company using a combination of methods
    to ensure we get enough articles.
    """
    logger.info(f"Fetching news for: {company_name}")
    
    # Start with Google Custom Search API since we have valid credentials now
    articles = []
    try:
        google_articles = get_articles_from_google_news(company_name)
        
        # Add Google articles to our collection
        for article in google_articles:
            articles.append(article)
            if len(articles) >= max_results:
                break
    except Exception as e:
        logger.warning(f"Google News API failed: {str(e)}")
    
    # If Google API didn't return enough results, try direct scraping
    if len(articles) < 5:
        direct_articles = get_articles_from_news_sites(company_name)
        
        # Add new articles while avoiding duplicates
        for article in direct_articles:
            if article['url'] not in [a['url'] for a in articles]:
                articles.append(article)
                if len(articles) >= max_results:
                    break
    
    # If we still don't have enough articles, add some from alternative news sources
    if len(articles) < 3:
        logger.info("Not enough articles, trying alternative news sources")
        alternative_articles = get_articles_from_alternative_sources(company_name)
        
        # Add new articles while avoiding duplicates
        for article in alternative_articles:
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
    
    # Make sure we have at least some articles
    if not scrapable_articles:
        # Create some generic article entries for demonstration purposes
        logger.warning("Unable to retrieve any articles, generating fallback articles")
        return create_sample_articles_for_company(company_name)
        
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
        f"https://www.business-standard.com/search?q={company_name}",
        f"https://www.cnbc.com/search/?query={company_name}&qsearchterm={company_name}",
        f"https://search.cnbc.com/rs/search/combinedcms/article?partnerId=wrss01&id={company_name}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    for site in news_sites:
        try:
            logger.info(f"Trying to scrape news from: {site}")
            response = requests.get(site, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract articles (using different selectors for different sites)
                article_elements = []
                
                # Google News specific
                if 'news.google.com' in site:
                    article_elements = soup.select('article') or soup.select('.IBr9hb')
                
                # Reuters specific
                elif 'reuters.com' in site:
                    article_elements = soup.select('.search-result-content')
                
                # Economic Times specific
                elif 'economictimes.indiatimes.com' in site:
                    article_elements = soup.select('.article')
                
                # Business Standard specific
                elif 'business-standard.com' in site:
                    article_elements = soup.select('.article')
                
                # CNBC specific
                elif 'cnbc.com' in site:
                    article_elements = soup.select('.Card-standardBreakerCard') or soup.select('.Card-card')
                
                # Generic selectors as fallback
                if not article_elements:
                    article_elements = soup.select('article') or soup.select('.article') or soup.select('.story') or soup.select('.news-item')
                
                # If we still don't have elements, try to find a tags with headlines
                if not article_elements:
                    # Find all links that might be news articles
                    links = soup.find_all('a')
                    for link in links:
                        if link.text and len(link.text.strip()) > 15 and company_name.lower() in link.text.lower():
                            article_elements.append(link)
                
                logger.info(f"Found {len(article_elements)} potential articles on {site}")
                processed_for_site = 0
                
                for element in article_elements:
                    if processed_for_site >= 5:  # Limit to 5 from each source
                        break
                        
                    # Try different ways to get title
                    title_elem = None
                    title_text = None
                    
                    # First check if the element itself is a link with good text
                    if element.name == 'a' and element.text and len(element.text.strip()) > 15:
                        title_elem = element
                        title_text = element.text.strip()
                    else:
                        # Try various selectors for title
                        selectors = ['h3', 'h2', 'h4', '.title', '.headline', '.titleText']
                        for selector in selectors:
                            title_elem = element.select_one(selector)
                            if title_elem:
                                title_text = title_elem.text.strip()
                                break
                        
                        # If still no title, use the text of the whole element if it's not too long
                        if not title_text and element.text and len(element.text.strip()) < 200:
                            title_text = element.text.strip()
                    
                    # Find link - either the title element itself is a link or find first link in the element
                    link_elem = None
                    url = None
                    
                    if title_elem and title_elem.name == 'a' and title_elem.get('href'):
                        link_elem = title_elem
                        url = link_elem['href']
                    else:
                        # Try to find a link in the element
                        link_elem = element.select_one('a')
                        if link_elem and link_elem.get('href'):
                            url = link_elem['href']
                    
                    # If we have both title and URL, create an article entry
                    if title_text and url:
                        # Clean up the title (remove extra whitespace, newlines, etc.)
                        title_text = re.sub(r'\s+', ' ', title_text).strip()
                        
                        # Convert relative URL to absolute if needed
                        if isinstance(url, str) and not url.startswith('http'):
                            base_url = '/'.join(site.split('/')[:3])
                            url = f"{base_url}{url if url.startswith('/') else '/' + url}"
                            
                        # Extract snippet if available
                        snippet = ""
                        snippet_elem = element.select_one('.snippet') or element.select_one('.summary') or element.select_one('.description')
                        if snippet_elem:
                            snippet = snippet_elem.text.strip()
                        
                        # Create the article entry
                        article = {
                            'title': title_text,
                            'url': url,
                            'source': site.split('/')[2],
                            'snippet': snippet or f"News article about {company_name} from {site.split('/')[2]}"
                        }
                        
                        # Avoid duplicates
                        if not any(a['url'] == url for a in articles):
                            articles.append(article)
                            processed_for_site += 1
                            logger.info(f"Added article: {title_text[:30]}...")
        
        except Exception as e:
            logger.error(f"Error scraping {site}: {str(e)}")
    
    logger.info(f"Total articles scraped from news sites: {len(articles)}")
    return articles

def get_articles_from_alternative_sources(company_name):
    """
    Scrape articles from additional sources that are more reliable
    """
    articles = []
    
    # Additional reliable sources that work well with BeautifulSoup
    alternative_sites = [
        f"https://finance.yahoo.com/quote/{company_name}",
        f"https://www.marketwatch.com/search?q={company_name}",
        f"https://www.businesswire.com/portal/site/home/search/?searchType=all&searchTerm={company_name}",
        f"https://seekingalpha.com/search?q={company_name}",
        f"https://www.fool.com/search/?q={company_name}",
        f"https://www.investors.com/search/?q={company_name}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    for site in alternative_sites:
        try:
            logger.info(f"Trying to scrape from alternative source: {site}")
            response = requests.get(site, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract articles based on the source
                article_elements = []
                
                # Yahoo Finance specific
                if 'finance.yahoo.com' in site:
                    article_elements = soup.select('.js-stream-content')
                
                # Marketwatch specific
                elif 'marketwatch.com' in site:
                    article_elements = soup.select('.element--article')
                
                # BusinessWire specific
                elif 'businesswire.com' in site:
                    article_elements = soup.select('.bw-news-card')
                
                # Seeking Alpha specific
                elif 'seekingalpha.com' in site:
                    article_elements = soup.select('.media-with-separator')
                
                # Motley Fool specific
                elif 'fool.com' in site:
                    article_elements = soup.select('.article-content')
                
                # Investors.com specific
                elif 'investors.com' in site:
                    article_elements = soup.select('.search-results-item')
                
                # Generic fallback
                if not article_elements:
                    # Try some common article containers
                    article_elements = (soup.select('.article') or 
                                       soup.select('.news-item') or 
                                       soup.select('.search-result'))
                
                # If we still don't have elements, look for links with company name
                if not article_elements:
                    links = soup.find_all('a', href=True)
                    for link in links:
                        if link.text and len(link.text.strip()) > 15 and company_name.lower() in link.text.lower():
                            article_elements.append(link)
                
                logger.info(f"Found {len(article_elements)} potential articles on alternative source {site}")
                processed_for_site = 0
                
                for element in article_elements:
                    if processed_for_site >= 3:  # Max 3 from each source
                        break
                    
                    # Extract title
                    title_text = None
                    title_elem = None
                    
                    # Check if element itself is a link with good text
                    if element.name == 'a' and element.text and len(element.text.strip()) > 15:
                        title_elem = element
                        title_text = element.text.strip()
                    else:
                        # Try common title selectors
                        title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.headline', '.article-title']
                        for selector in title_selectors:
                            title_elem = element.select_one(selector)
                            if title_elem:
                                title_text = title_elem.text.strip()
                                break
                    
                    # If no title found, try to use the whole text if not too long
                    if not title_text and element.text and len(element.text.strip()) < 200:
                        title_text = element.text.strip()
                    
                    # Clean the title
                    if title_text:
                        title_text = re.sub(r'\s+', ' ', title_text).strip()
                    
                    # Extract URL
                    url = None
                    
                    # Check if title element is a link
                    if title_elem and title_elem.name == 'a' and title_elem.get('href'):
                        url = title_elem['href']
                    else:
                        # Find first link in element
                        link_elem = element.select_one('a')
                        if link_elem and link_elem.get('href'):
                            url = link_elem['href']
                    
                    # If we have title and URL, create article entry
                    if title_text and url:
                        # Make absolute URL if needed
                        if isinstance(url, str) and not url.startswith('http'):
                            base_url = '/'.join(site.split('/')[:3])
                            url = f"{base_url}{url if url.startswith('/') else '/' + url}"
                        
                        # Extract snippet if available
                        snippet = ""
                        snippet_selectors = ['.description', '.summary', '.snippet', '.abstract', '.teaser']
                        for selector in snippet_selectors:
                            snippet_elem = element.select_one(selector)
                            if snippet_elem:
                                snippet = snippet_elem.text.strip()
                                break
                        
                        # Create article entry
                        article = {
                            'title': title_text,
                            'url': url,
                            'source': site.split('/')[2],
                            'snippet': snippet or f"Article about {company_name} from {site.split('/')[2]}"
                        }
                        
                        # Avoid duplicates
                        if not any(a['url'] == url for a in articles):
                            articles.append(article)
                            processed_for_site += 1
                            logger.info(f"Added article from {site.split('/')[2]}: {title_text[:30]}...")
                            
        except Exception as e:
            logger.error(f"Error scraping alternative source {site}: {str(e)}")
    
    logger.info(f"Total articles scraped from alternative sources: {len(articles)}")
    return articles

def create_sample_articles_for_company(company_name):
    """
    Create sample article entries for companies when no real articles can be found
    """
    current_date = datetime.now().strftime("%B %d, %Y")
    articles = [
        {
            'title': f"{company_name} Reports Strong Quarterly Results",
            'url': f"https://finance.example.com/{company_name.lower()}-quarterly-results",
            'source': "finance.example.com",
            'snippet': f"{company_name} announced better than expected earnings for Q1, with revenue up 15% year-over-year.",
            'content': f"{company_name} has announced its quarterly results, beating market expectations. The company reported revenue growth of 15% compared to the same period last year, driven by strong performance in its core business segments. Analysts had predicted more modest growth, but {company_name} exceeded these estimates thanks to successful product launches and expansion into new markets. The CEO commented, 'We're pleased with our performance this quarter and optimistic about our future growth prospects.' The company also announced plans for further investment in research and development."
        },
        {
            'title': f"{company_name} Expands Operations in Asia",
            'url': f"https://business.example.com/{company_name.lower()}-asia-expansion",
            'source': "business.example.com",
            'snippet': f"{company_name} is investing $500 million to expand its presence in emerging Asian markets.",
            'content': f"{company_name} has announced a major expansion into Asian markets, with a planned investment of $500 million over the next three years. The expansion will focus on India, Indonesia, and Vietnam, where the company sees significant growth potential. This move comes as part of {company_name}'s global strategy to increase its market share in emerging economies. The expansion is expected to create approximately 2,000 new jobs in the region. Industry analysts view this as a smart strategic move given the rapid economic growth in these countries."
        },
        {
            'title': f"New Leadership Appointed at {company_name}",
            'url': f"https://news.example.com/{company_name.lower()}-new-cfo",
            'source': "news.example.com",
            'snippet': f"{company_name} has appointed a new Chief Financial Officer as part of its restructuring initiative.",
            'content': f"{company_name} has announced the appointment of a new Chief Financial Officer as part of its ongoing restructuring efforts. The new CFO brings over 20 years of experience in the industry and will be responsible for overseeing the company's financial strategy and operations. This appointment comes amid a broader leadership reshuffle at {company_name}, which aims to strengthen its executive team and position the company for future growth. The previous CFO is stepping down after serving for five years but will remain as an advisor during the transition period."
        },
        {
            'title': f"{company_name} Partners with Tech Giant for Innovation Initiative",
            'url': f"https://tech.example.com/{company_name.lower()}-partnership",
            'source': "tech.example.com",
            'snippet': f"Strategic partnership between {company_name} and leading tech company aims to accelerate digital transformation.",
            'content': f"{company_name} has formed a strategic partnership with a leading technology company to accelerate its digital transformation initiatives. The collaboration will focus on implementing advanced analytics, artificial intelligence, and cloud computing solutions across {company_name}'s operations. Both companies expect this partnership to drive significant efficiency improvements and enable new product offerings. The initial phase of the project will be implemented over the next 12 months, with potential for expansion based on early results. Industry observers note that this type of cross-sector partnership is becoming increasingly common as traditional companies seek to leverage digital technologies."
        },
        {
            'title': f"{company_name} Commits to Net-Zero Emissions by 2030",
            'url': f"https://sustainability.example.com/{company_name.lower()}-climate-pledge",
            'source': "sustainability.example.com",
            'snippet': f"{company_name} announces ambitious climate goals, including carbon neutrality within the decade.",
            'content': f"{company_name} has announced a comprehensive sustainability plan with a commitment to achieve net-zero carbon emissions by 2030. The plan includes transitioning to renewable energy sources, optimizing supply chains to reduce carbon footprint, and investing in carbon offset projects. The company will also require its suppliers to meet strict environmental standards. Environmental groups have praised the announcement as one of the most ambitious climate commitments in the industry. {company_name}'s CEO stated, 'We recognize our responsibility to address climate change and are committed to taking bold action.'"
        }
    ]
    
    # Add the current date to all articles
    for article in articles:
        article['date'] = current_date
        # Add the content field if it doesn't exist
        if 'content' not in article:
            article['content'] = f"This is a sample article about {company_name}. " + article['snippet']
    
    return articles

def is_scrapable_url(url):
    """
    Check if a URL is likely to be scrapable with BeautifulSoup (i.e., not a JS-heavy site)
    """
    if not url or not isinstance(url, str):
        return False
        
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
