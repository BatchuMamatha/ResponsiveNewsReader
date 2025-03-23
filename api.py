from fastapi import FastAPI, HTTPException, Request
import uvicorn
from pydantic import BaseModel
import utils
import news_scraper
import sentiment_analyzer
import tts_generator
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="News Summarization API",
              description="API for news extraction, sentiment analysis, and TTS generation")

class CompanyRequest(BaseModel):
    company_name: str

class TTSRequest(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"message": "News Summarization and Analysis API"}

@app.post("/get_news")
async def get_news(request: CompanyRequest):
    try:
        logger.info(f"Fetching news for company: {request.company_name}")
        
        # Get news articles
        articles = news_scraper.get_news_articles(request.company_name)
        
        if not articles or len(articles) == 0:
            logger.warning(f"No articles found for {request.company_name}, using sample articles")
            articles = news_scraper.create_sample_articles_for_company(request.company_name)
        
        # Process articles (max 10)
        processed_articles = []
        for article in articles[:10]:
            try:
                # Check if article already has content (for sample articles)
                if 'content' in article and article['content']:
                    content = article['content']
                else:
                    # Extract content and perform sentiment analysis
                    content = news_scraper.extract_article_content(article['url'])
                
                if not content:
                    logger.warning(f"Failed to extract content from {article.get('url', 'unknown URL')}")
                    continue
                    
                sentiment_result = sentiment_analyzer.analyze_sentiment(content)
                topics = sentiment_analyzer.extract_topics(content)
                
                processed_article = {
                    "Title": article['title'],
                    "URL": article.get('url', ''),
                    "Source": article.get('source', 'Unknown'),
                    "Summary": utils.summarize_text(content),
                    "Sentiment": sentiment_result.get('sentiment', 'Neutral'),
                    "Sentiment_Score": sentiment_result.get('compound', 0),
                    "Topics": topics
                }
                
                processed_articles.append(processed_article)
            except Exception as article_e:
                logger.error(f"Error processing article {article.get('title', 'unknown')}: {str(article_e)}")
                continue
        
        if not processed_articles:
            logger.warning("No articles could be processed successfully")
            # Create a basic response with minimal information
            return {
                "Company": request.company_name,
                "Articles": [],
                "Message": "Unable to process articles for this company. Please try another company name."
            }
        
        # Generate comparative analysis
        comparative_analysis = sentiment_analyzer.generate_comparative_analysis(processed_articles)
        
        # Final sentiment analysis summary
        final_sentiment = sentiment_analyzer.generate_final_sentiment_summary(processed_articles)
        
        # Prepare response
        response = {
            "Company": request.company_name,
            "Articles": processed_articles,
            "Comparative Sentiment Score": comparative_analysis,
            "Final Sentiment Analysis": final_sentiment
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/generate_tts")
async def generate_tts(request: TTSRequest):
    try:
        logger.info(f"Generating TTS for text: {request.text[:50]}...")
        
        # Generate TTS
        audio_base64 = tts_generator.generate_hindi_tts(request.text)
        
        return {"audio_base64": audio_base64}
        
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
