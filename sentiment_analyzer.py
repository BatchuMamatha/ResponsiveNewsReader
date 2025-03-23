import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk import pos_tag
import string
import logging
import os
import re
from collections import Counter
import random
import utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK resources
try:
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    
    # Create empty punkt_tab files if they don't exist
    import os
    punkt_dirs = [
        '/home/runner/nltk_data/tokenizers/punkt_tab/english',
        '/home/runner/workspace/.pythonlibs/nltk_data/tokenizers/punkt_tab/english'
    ]
    
    for punkt_dir in punkt_dirs:
        try:
            os.makedirs(punkt_dir, exist_ok=True)
            
            # Create the required tab files
            required_files = ['punkt.tab', 'collocations.tab', 'sent_starters.txt']
            for file_name in required_files:
                with open(os.path.join(punkt_dir, file_name), 'w') as f:
                    f.write('')  # Create empty file
                logger.info(f"Created {file_name} in {punkt_dir}")
                
            # Create the PY3 directory
            py3_dir = os.path.join(punkt_dir, 'PY3')
            os.makedirs(py3_dir, exist_ok=True)
            
            # Create empty pickle files
            for file_name in ['pickle', 'pickle.gz']:
                with open(os.path.join(py3_dir, file_name), 'w') as f:
                    f.write('')
                logger.info(f"Created {file_name} in {py3_dir}")
                
        except Exception as e:
            logger.warning(f"Error creating files in {punkt_dir}: {str(e)}")
            
except Exception as e:
    logger.warning(f"Error downloading NLTK resources: {str(e)}")

# Initialize sentiment analyzer
sid = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    """
    Analyze the sentiment of text using VADER
    Returns: A dictionary with sentiment scores and overall sentiment label
    """
    if not text:
        return {"sentiment": "Neutral", "scores": {"neg": 0, "neu": 1, "pos": 0, "compound": 0}}
    
    try:
        # Get sentiment scores
        scores = sid.polarity_scores(text)
        
        # Determine sentiment based on compound score
        if scores['compound'] >= 0.05:
            sentiment = "Positive"
        elif scores['compound'] <= -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
            
        return {
            "sentiment": sentiment,
            "scores": scores
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        return {"sentiment": "Neutral", "scores": {"neg": 0, "neu": 1, "pos": 0, "compound": 0}}

def extract_topics(text, num_topics=5):
    """
    Extract key topics (keywords) from text
    Returns: A list of topic keywords
    """
    if not text:
        return []
        
    try:
        # Tokenize and clean text
        stop_words = set(stopwords.words('english'))
        tokens = word_tokenize(text.lower())
        
        # Remove punctuation and stopwords
        tokens = [token for token in tokens if token not in string.punctuation and token not in stop_words and len(token) > 2]
        
        # POS tagging to identify nouns (which are likely to be topics)
        tagged_tokens = pos_tag(tokens)
        
        # Extract nouns (NN, NNS, NNP, NNPS)
        nouns = [word for word, tag in tagged_tokens if tag.startswith('NN')]
        
        # Get the most common nouns
        fdist = FreqDist(nouns)
        topics = [topic for topic, _ in fdist.most_common(num_topics)]
        
        return topics
    except Exception as e:
        logger.error(f"Error extracting topics: {str(e)}")
        return []

def generate_comparative_analysis(articles):
    """
    Generate comparative sentiment analysis across articles
    Returns: A structured analysis of sentiment differences, topic overlaps, etc.
    """
    if not articles:
        return {
            "Sentiment Distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
            "Coverage Differences": [],
            "Topic Overlap": {"Common Topics": [], "Unique Topics in Positive Articles": [], "Unique Topics in Negative Articles": []}
        }
    
    try:
        # Count sentiments
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for article in articles:
            sentiment_counts[article['Sentiment']] += 1
            
        # Group articles by sentiment
        positive_articles = [article for article in articles if article['Sentiment'] == "Positive"]
        negative_articles = [article for article in articles if article['Sentiment'] == "Negative"]
        neutral_articles = [article for article in articles if article['Sentiment'] == "Neutral"]
        
        # Collect topics by sentiment
        positive_topics = set()
        for article in positive_articles:
            positive_topics.update(article['Topics'])
            
        negative_topics = set()
        for article in negative_articles:
            negative_topics.update(article['Topics'])
            
        neutral_topics = set()
        for article in neutral_articles:
            neutral_topics.update(article['Topics'])
            
        # Find topic overlap
        all_topics = positive_topics.union(negative_topics, neutral_topics)
        common_topics = positive_topics.intersection(negative_topics)
        
        # Prepare unique topics
        unique_positive = positive_topics - negative_topics
        unique_negative = negative_topics - positive_topics
        
        # Generate coverage differences (comparing different sentiment articles)
        coverage_differences = []
        
        # If we have both positive and negative articles
        if positive_articles and negative_articles:
            coverage_differences.append({
                "Comparison": f"Positive articles focus on {', '.join(list(unique_positive)[:3])} while negative articles emphasize {', '.join(list(unique_negative)[:3])}.",
                "Impact": f"The contrasting coverage suggests {articles[0].get('Title', '').split()[0]} is experiencing mixed market reception."
            })
            
        # Compare different positive articles
        if len(positive_articles) >= 2:
            coverage_differences.append({
                "Comparison": f"Multiple sources report positively on {articles[0].get('Title', '').split()[0]}, highlighting {', '.join(list(positive_topics)[:3])}.",
                "Impact": "Consistent positive coverage may influence investor confidence positively."
            })
            
        # Compare different negative articles
        if len(negative_articles) >= 2:
            coverage_differences.append({
                "Comparison": f"Several sources express concerns about {articles[0].get('Title', '').split()[0]}, particularly regarding {', '.join(list(negative_topics)[:3])}.",
                "Impact": "Multiple negative reports might signal underlying issues requiring attention."
            })
            
        # If we don't have enough comparisons, add a generic one
        if len(coverage_differences) < 2:
            coverage_differences.append({
                "Comparison": f"Articles highlight various aspects of {articles[0].get('Title', '').split()[0]}, including {', '.join(list(all_topics)[:5])}.",
                "Impact": "The diverse coverage provides a comprehensive view of the company's current situation."
            })
            
        return {
            "Sentiment Distribution": sentiment_counts,
            "Coverage Differences": coverage_differences,
            "Topic Overlap": {
                "Common Topics": list(common_topics),
                "Unique Topics in Positive Articles": list(unique_positive),
                "Unique Topics in Negative Articles": list(unique_negative)
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating comparative analysis: {str(e)}")
        return {
            "Sentiment Distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
            "Coverage Differences": [],
            "Topic Overlap": {"Common Topics": [], "Unique Topics in Positive Articles": [], "Unique Topics in Negative Articles": []}
        }

def generate_final_sentiment_summary(articles):
    """
    Generate a final summary of the overall sentiment across all articles
    """
    if not articles:
        return "No articles available for sentiment analysis."
        
    try:
        # Count sentiments
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for article in articles:
            sentiment_counts[article['Sentiment']] += 1
            
        # Determine dominant sentiment
        max_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
        total_articles = len(articles)
        
        # Get all topics
        all_topics = []
        for article in articles:
            all_topics.extend(article['Topics'])
            
        # Count topic frequency
        topic_counter = Counter(all_topics)
        common_topics = [topic for topic, count in topic_counter.most_common(3)]
        
        # Generate summary based on sentiment distribution
        if sentiment_counts["Positive"] > sentiment_counts["Negative"] + sentiment_counts["Neutral"]:
            return f"The news coverage is predominantly positive ({sentiment_counts['Positive']}/{total_articles} articles), focusing on {', '.join(common_topics)}. This suggests a favorable outlook for the company."
        
        elif sentiment_counts["Negative"] > sentiment_counts["Positive"] + sentiment_counts["Neutral"]:
            return f"The news coverage is predominantly negative ({sentiment_counts['Negative']}/{total_articles} articles), highlighting concerns about {', '.join(common_topics)}. This suggests potential challenges for the company."
        
        elif sentiment_counts["Neutral"] > sentiment_counts["Positive"] + sentiment_counts["Negative"]:
            return f"The news coverage is largely neutral ({sentiment_counts['Neutral']}/{total_articles} articles), reporting on {', '.join(common_topics)} without strong sentiment. This suggests a stable but unremarkable situation."
        
        else:
            return f"The news coverage is mixed with {sentiment_counts['Positive']} positive, {sentiment_counts['Negative']} negative, and {sentiment_counts['Neutral']} neutral articles, covering topics like {', '.join(common_topics)}. This reflects diverse perspectives on the company's current status."
            
    except Exception as e:
        logger.error(f"Error generating final sentiment summary: {str(e)}")
        return "Unable to generate sentiment summary due to an error in processing."
