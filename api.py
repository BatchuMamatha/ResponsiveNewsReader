from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
import uvicorn
from typing import Dict, List, Any
import os
import json
import logging
from utils import sanitize_company_name
from news_scraper import get_news_articles
from sentiment_analyzer import analyze_sentiment, generate_comparative_analysis
from tts_service import generate_hindi_tts

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="News Summarization and TTS API",
    description="API for extracting, analyzing news articles and generating Hindi TTS",
    version="1.0.0"
)

# In-memory cache for results to avoid repeated scraping and analysis
results_cache = {}

@app.get("/")
def read_root():
    return {"message": "Welcome to the News Summarization and TTS API", 
            "endpoints": ["/news/{company_name}", "/tts/{company_name}"]}

@app.get("/news/{company_name}")
async def get_news_analysis(company_name: str):
    try:
        # Sanitize company name
        company_name = sanitize_company_name(company_name)
        
        # Check if we have results cached
        if company_name in results_cache:
            logger.info(f"Returning cached results for {company_name}")
            return results_cache[company_name]
        
        # Get news articles
        logger.info(f"Fetching news articles for {company_name}")
        articles = get_news_articles(company_name)
        
        if not articles or len(articles) == 0:
            raise HTTPException(status_code=404, detail=f"No news articles found for {company_name}")
        
        # Analyze sentiment for each article
        logger.info(f"Analyzing sentiment for {len(articles)} articles")
        for article in articles:
            article.update(analyze_sentiment(article.get("Summary", "")))
        
        # Generate comparative analysis
        logger.info("Generating comparative analysis")
        comparative_analysis = generate_comparative_analysis(articles)
        
        # Create final response
        result = {
            "Company": company_name,
            "Articles": articles,
            "Comparative Sentiment Score": comparative_analysis,
            "Final Sentiment Analysis": generate_final_sentiment_analysis(comparative_analysis)
        }
        
        # Cache the results
        results_cache[company_name] = result
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing request for {company_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/tts/{company_name}")
async def get_hindi_tts(company_name: str):
    try:
        # Sanitize company name
        company_name = sanitize_company_name(company_name)
        
        # First make sure we have the news analysis
        if company_name not in results_cache:
            logger.info(f"News analysis not in cache for {company_name}, fetching it first")
            await get_news_analysis(company_name)
        
        # Generate Hindi TTS
        logger.info(f"Generating Hindi TTS for {company_name}")
        news_data = results_cache[company_name]
        text_content = generate_tts_content(news_data)
        
        # Convert to Hindi speech
        audio_content = generate_hindi_tts(text_content)
        
        return Response(content=audio_content, media_type="audio/mp3")
    
    except Exception as e:
        logger.error(f"Error generating TTS for {company_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")

def generate_final_sentiment_analysis(comparative_analysis: Dict[str, Any]) -> str:
    """Generate a final sentiment analysis based on the comparative analysis results"""
    try:
        sentiment_dist = comparative_analysis.get("Sentiment Distribution", {})
        positive = sentiment_dist.get("Positive", 0)
        negative = sentiment_dist.get("Negative", 0)
        neutral = sentiment_dist.get("Neutral", 0)
        
        total = positive + negative + neutral
        if total == 0:
            return "No sentiment analysis available."
        
        positive_percent = (positive / total) * 100
        negative_percent = (negative / total) * 100
        
        if positive_percent > 60:
            return "News coverage is predominantly positive. Favorable outlook suggested."
        elif negative_percent > 60:
            return "News coverage is predominantly negative. Caution advised."
        elif positive_percent > negative_percent:
            return "News coverage is slightly more positive than negative. Moderately favorable outlook."
        elif negative_percent > positive_percent:
            return "News coverage is slightly more negative than positive. Some concerns present."
        else:
            return "News coverage is balanced between positive and negative sentiments. Mixed outlook."
    
    except Exception as e:
        logger.error(f"Error generating final sentiment analysis: {str(e)}")
        return "Unable to generate final sentiment analysis."

def generate_tts_content(news_data: Dict[str, Any]) -> str:
    """Generate content for text-to-speech conversion"""
    try:
        company = news_data.get("Company", "the company")
        final_sentiment = news_data.get("Final Sentiment Analysis", "No analysis available")
        
        # Create a concise summary for TTS
        tts_content = f"{company} के समाचार विश्लेषण के परिणाम। "  # Results of news analysis for [company]
        tts_content += f"हमने {len(news_data.get('Articles', []))} समाचार लेख पाए। "  # We found [n] news articles
        
        # Add sentiment distribution
        sentiment_dist = news_data.get("Comparative Sentiment Score", {}).get("Sentiment Distribution", {})
        positive = sentiment_dist.get("Positive", 0)
        negative = sentiment_dist.get("Negative", 0)
        neutral = sentiment_dist.get("Neutral", 0)
        
        tts_content += f"इनमें से {positive} सकारात्मक, {negative} नकारात्मक, और {neutral} तटस्थ हैं। "  # Of these, [n] are positive, [n] are negative, and [n] are neutral
        
        # Add final sentiment analysis
        tts_content += f"समग्र विश्लेषण: {final_sentiment} "  # Overall analysis: [final_sentiment]
        
        # Add top headlines
        tts_content += "मुख्य समाचार शीर्षक: "  # Top news headlines:
        for i, article in enumerate(news_data.get("Articles", [])[:3]):  # Only include top 3 articles
            tts_content += f"{i+1}. {article.get('Title', 'No title')}। "
        
        return tts_content
    
    except Exception as e:
        logger.error(f"Error generating TTS content: {str(e)}")
        return f"समाचार विश्लेषण में त्रुटि हुई है। कृपया बाद में पुन: प्रयास करें।"  # Error in news analysis. Please try again later.

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
