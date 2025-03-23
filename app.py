import streamlit as st
import requests
import json
import base64
import os
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="News Analyzer & Hindi TTS",
    page_icon="📰",
    layout="wide"
)

# API endpoint (when running locally)
API_BASE_URL = "http://localhost:8000"

# Function to get a list of predefined companies
def get_companies():
    return [
        "Amazon", "Apple", "Google", "Microsoft", "Tesla", 
        "Meta", "Netflix", "Uber", "Twitter", "Nvidia",
        "Reliance", "Tata", "Infosys", "Wipro", "TCS"
    ]

# Function to call the API to get news articles
def get_news_data(company_name):
    try:
        response = requests.get(f"{API_BASE_URL}/news/{company_name}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching news data: {str(e)}")
        return None

# Function to play audio
def get_audio_player(company_name):
    try:
        response = requests.get(f"{API_BASE_URL}/tts/{company_name}")
        response.raise_for_status()
        audio_data = response.content
        
        # Create a base64 encoded string for the audio
        b64_audio = base64.b64encode(audio_data).decode('utf-8')
        
        # Create an audio player HTML component
        audio_html = f"""
        <audio controls>
            <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        return audio_html
    except requests.RequestException as e:
        st.error(f"Error generating audio: {str(e)}")
        return None

# Main app function
def main():
    # App title and description
    st.title("📰 News Summarization & Hindi Text-to-Speech")
    st.markdown("""
    This application extracts key details from multiple news articles related to a company,
    performs sentiment analysis, conducts a comparative analysis, and generates a
    text-to-speech (TTS) output in Hindi.
    """)
    
    # Sidebar for input
    st.sidebar.title("Search Options")
    
    # Option to either select from dropdown or enter custom company name
    input_method = st.sidebar.radio(
        "Choose input method:",
        ("Select from list", "Enter company name")
    )
    
    company_name = None
    if input_method == "Select from list":
        company_name = st.sidebar.selectbox(
            "Select a company:",
            get_companies()
        )
    else:
        company_name = st.sidebar.text_input("Enter company name:")
    
    # Search button
    search_button = st.sidebar.button("Analyze News")
    
    # Only process if a company name is provided and search button is clicked
    if company_name and search_button:
        # Show loading spinner
        with st.spinner(f"Fetching and analyzing news for {company_name}..."):
            # Get news data
            news_data = get_news_data(company_name)
            
            if news_data:
                # Display results
                st.header(f"Analysis Results for {company_name}")
                
                # Display audio player for Hindi TTS
                st.subheader("📢 Hindi Audio Summary")
                audio_player = get_audio_player(company_name)
                if audio_player:
                    st.markdown(audio_player, unsafe_allow_html=True)
                
                # Display company sentiment overview
                st.subheader("📊 Overall Sentiment Analysis")
                
                # Create columns for displaying sentiment distribution
                col1, col2, col3 = st.columns(3)
                
                sentiment_distribution = news_data.get("Comparative Sentiment Score", {}).get("Sentiment Distribution", {})
                positive_count = sentiment_distribution.get("Positive", 0)
                negative_count = sentiment_distribution.get("Negative", 0)
                neutral_count = sentiment_distribution.get("Neutral", 0)
                
                col1.metric("Positive", positive_count)
                col2.metric("Negative", negative_count)
                col3.metric("Neutral", neutral_count)
                
                # Display final sentiment analysis
                st.markdown(f"**Final Assessment:** {news_data.get('Final Sentiment Analysis', 'No analysis available')}")
                
                # Display articles
                st.subheader("📰 News Articles")
                
                for idx, article in enumerate(news_data.get("Articles", [])):
                    with st.expander(f"Article {idx+1}: {article.get('Title', 'No title')}"):
                        st.markdown(f"**Summary:** {article.get('Summary', 'No summary available')}")
                        
                        # Display sentiment with appropriate color
                        sentiment = article.get('Sentiment', 'Unknown')
                        sentiment_color = {
                            'Positive': 'green',
                            'Negative': 'red',
                            'Neutral': 'blue'
                        }.get(sentiment, 'gray')
                        
                        st.markdown(f"**Sentiment:** <span style='color:{sentiment_color}'>{sentiment}</span>", 
                                   unsafe_allow_html=True)
                        
                        # Display topics as tags
                        st.markdown("**Topics:**")
                        topics_html = ""
                        for topic in article.get('Topics', []):
                            topics_html += f"<span style='background-color:#f0f2f6;padding:2px 8px;margin:0 4px;border-radius:12px;font-size:0.8em'>{topic}</span>"
                        
                        st.markdown(topics_html, unsafe_allow_html=True)
                
                # Display comparative analysis
                st.subheader("🔍 Comparative Analysis")
                
                # Topic overlap
                topic_overlap = news_data.get("Comparative Sentiment Score", {}).get("Topic Overlap", {})
                if topic_overlap:
                    with st.expander("Topic Distribution Across Articles"):
                        st.markdown("**Common Topics:**")
                        common_topics = ", ".join(topic_overlap.get("Common Topics", ["None"]))
                        st.write(common_topics)
                        
                        st.markdown("**Unique Topics:**")
                        unique_topics = []
                        for i, article in enumerate(news_data.get("Articles", [])):
                            unique_key = f"Unique Topics in Article {i+1}"
                            if unique_key in topic_overlap:
                                unique_topics.extend([f"{topic} (Article {i+1})" for topic in topic_overlap[unique_key]])
                        
                        if unique_topics:
                            st.write(", ".join(unique_topics))
                        else:
                            st.write("None")
                
                # Coverage differences
                coverage_differences = news_data.get("Comparative Sentiment Score", {}).get("Coverage Differences", [])
                if coverage_differences:
                    with st.expander("Coverage Differences and Impact"):
                        for diff in coverage_differences:
                            st.markdown(f"**Comparison:** {diff.get('Comparison', 'N/A')}")
                            st.markdown(f"**Impact:** {diff.get('Impact', 'N/A')}")
                            st.markdown("---")
            else:
                st.error("Unable to retrieve news data. Please try again.")
    
    # Display instructions when no company is selected yet
    if not search_button or not company_name:
        st.info("👈 Enter a company name in the sidebar and click 'Analyze News' to get started.")
        st.markdown("""
        ### How it works:
        1. Enter or select a company name
        2. The system fetches news articles about the company
        3. Sentiment analysis is performed on each article
        4. A comparative analysis is generated
        5. The summary is converted to Hindi speech
        """)

if __name__ == "__main__":
    main()
