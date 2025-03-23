import streamlit as st
import json
import requests
import base64
import pandas as pd
import time
import os

st.set_page_config(
    page_title="News Summarization & Sentiment Analysis",
    page_icon="📰",
    layout="wide"
)

# API endpoint (FastAPI backend)
API_ENDPOINT = "http://0.0.0.0:8000"

def get_company_news(company_name):
    """Get news articles for a company using the backend API"""
    try:
        response = requests.post(
            f"{API_ENDPOINT}/get_news", 
            json={"company_name": company_name},
            timeout=120  # Longer timeout for web scraping
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching news: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def generate_tts(text):
    """Generate Hindi TTS for the given text"""
    try:
        response = requests.post(
            f"{API_ENDPOINT}/generate_tts", 
            json={"text": text}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error generating TTS: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# UI Layout
st.title("📰 News Summarization & Sentiment Analysis")
st.markdown("""
This application extracts news articles about a company, performs sentiment analysis,
and generates a Hindi text-to-speech summary of the news coverage.
""")

# Company input
st.subheader("Enter Company Name")
sample_companies = ["Tesla", "Apple", "Google", "Microsoft", "Amazon", "Meta", "Samsung", "Reliance", "Tata"]
company_name = st.selectbox("Select or enter a company name", options=[""] + sample_companies, index=0)
custom_company = st.text_input("Or enter a custom company name")

# Use custom company if provided, otherwise use the selected one
if custom_company:
    company_name = custom_company

# Search button
search_clicked = st.button("Search News", type="primary", disabled=not company_name)

if search_clicked and company_name:
    with st.spinner(f"Searching for news about {company_name}..."):
        # Display a progress bar
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.05)  # Simulating the search process
            progress_bar.progress(i + 1)
        
        # Get news data
        news_data = get_company_news(company_name)
        
    if news_data:
        st.success(f"Found {len(news_data['Articles'])} news articles for {company_name}")
        
        # Display sentiment distribution
        st.subheader("Sentiment Analysis Summary")
        
        # Check if Comparative Sentiment Score exists
        if "Comparative Sentiment Score" in news_data and "Sentiment Distribution" in news_data["Comparative Sentiment Score"]:
            sentiment_dist = news_data["Comparative Sentiment Score"]["Sentiment Distribution"]
            
            # Create sentiment distribution dataframe for chart
            sentiment_df = pd.DataFrame({
                'Sentiment': list(sentiment_dist.keys()),
                'Count': list(sentiment_dist.values())
            })
            
            # Display as a bar chart
            st.bar_chart(sentiment_df.set_index('Sentiment'))
        else:
            # Create a generic sentiment distribution based on available articles
            sentiments = {"Positive": 0, "Negative": 0, "Neutral": 0}
            for article in news_data.get("Articles", []):
                if "Sentiment" in article:
                    sentiments[article["Sentiment"]] += 1
            
            # Display as a bar chart
            sentiment_df = pd.DataFrame({
                'Sentiment': list(sentiments.keys()),
                'Count': list(sentiments.values())
            })
            st.bar_chart(sentiment_df.set_index('Sentiment'))
            
        # Display Final Sentiment
        st.subheader("Overall Sentiment Analysis")
        if "Final Sentiment Analysis" in news_data:
            st.info(news_data["Final Sentiment Analysis"])
        else:
            st.info("No detailed sentiment analysis available for this search.")
        
        # Generate and display TTS
        st.subheader("Text-to-Speech Summary (Hindi)")
        
        # Extract a summary for TTS
        if "Final Sentiment Analysis" in news_data:
            tts_summary = f"{company_name} के बारे में समाचार विश्लेषण: {news_data['Final Sentiment Analysis']}"
        else:
            tts_summary = f"{company_name} के बारे में समाचार विश्लेषण: कंपनी के बारे में मिली-जुली ख़बरें हैं।"
        
        with st.spinner("Generating Hindi audio..."):
            tts_result = generate_tts(tts_summary)
            
        if tts_result and 'audio_base64' in tts_result:
            st.audio(base64.b64decode(tts_result['audio_base64']), format='audio/mp3')
        else:
            st.warning("Audio generation failed. Please try again.")
        
        # Articles tab
        st.subheader("News Articles")
        
        # Check if there are any articles
        if news_data.get('Articles') and len(news_data['Articles']) > 0:
            # Create tabs for each article
            tabs = st.tabs([f"Article {i+1}" for i in range(len(news_data['Articles']))])
            
            # Display article details in each tab
            for i, (tab, article) in enumerate(zip(tabs, news_data['Articles'])):
                with tab:
                    st.markdown(f"### {article['Title']}")
                    
                    # Create columns for metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        sentiment_color = {
                            'Positive': 'green',
                            'Negative': 'red',
                            'Neutral': 'blue'
                        }
                        sentiment = article.get('Sentiment', 'Neutral')
                        st.markdown(f"**Sentiment:** <span style='color:{sentiment_color.get(sentiment, 'blue')}'>{sentiment}</span>", unsafe_allow_html=True)
                    
                    with col2:
                        topics = article.get('Topics', [])
                        if topics:
                            st.markdown(f"**Topics:** {', '.join(topics)}")
                        else:
                            st.markdown("**Topics:** None")
                    
                    st.markdown("**Summary:**")
                    summary = article.get('Summary', 'No summary available.')
                    st.markdown(f"{summary}")
        else:
            st.warning("No articles were found for this company. Try another company name or check if the Google API key is valid.")
                
        # Comparative Analysis
        st.subheader("Comparative Analysis")
        
        # Check if Comparative Sentiment Score exists
        if "Comparative Sentiment Score" in news_data:
            # Topic overlap
            st.markdown("### Topic Coverage")
            if "Topic Overlap" in news_data["Comparative Sentiment Score"]:
                topic_overlap = news_data["Comparative Sentiment Score"]["Topic Overlap"]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Common Topics**")
                    if "Common Topics" in topic_overlap:
                        st.write(", ".join(topic_overlap["Common Topics"]) if topic_overlap["Common Topics"] else "None")
                    else:
                        st.write("None")
                
                with col2:
                    st.markdown("**Unique Topics (Positive Articles)**")
                    if "Unique Topics in Positive Articles" in topic_overlap:
                        st.write(", ".join(topic_overlap["Unique Topics in Positive Articles"]))
                    else:
                        st.write("Not available")
                        
                with col3:
                    st.markdown("**Unique Topics (Negative Articles)**")
                    if "Unique Topics in Negative Articles" in topic_overlap:
                        st.write(", ".join(topic_overlap["Unique Topics in Negative Articles"]))
                    else:
                        st.write("Not available")
            else:
                st.info("No detailed topic coverage analysis available.")
            
            # Coverage differences
            st.markdown("### Coverage Differences")
            if "Coverage Differences" in news_data["Comparative Sentiment Score"]:
                coverage_diffs = news_data["Comparative Sentiment Score"]["Coverage Differences"]
                if coverage_diffs:
                    for idx, comparison in enumerate(coverage_diffs):
                        with st.expander(f"Comparison {idx+1}"):
                            st.markdown(f"**Comparison:** {comparison.get('Comparison', 'Not available')}")
                            st.markdown(f"**Impact:** {comparison.get('Impact', 'Not available')}")
                else:
                    st.info("No coverage differences analysis available.")
            else:
                st.info("No coverage differences analysis available.")
        else:
            st.info("Detailed comparative analysis not available for this search.")
        
        # Show raw JSON data in an expander
        with st.expander("Show Raw JSON Data"):
            st.json(news_data)
    else:
        st.error(f"No news data found for {company_name}")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit • Powered by BeautifulSoup and NLTK")
