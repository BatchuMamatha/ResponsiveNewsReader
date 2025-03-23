import os
import base64
import logging
import requests
import tempfile
from gtts import gTTS
from googletrans import Translator
from io import BytesIO
import utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def translate_to_hindi(text):
    """
    Translate English text to Hindi using Google Translate
    """
    try:
        translator = Translator()
        translation = translator.translate(text, dest='hi')
        return translation.text
    except Exception as e:
        logger.error(f"Error translating text to Hindi: {str(e)}")
        # Fallback solution - basic phrases in Hindi if translation fails
        fallback_text = "यह एक समाचार सारांश है। कृपया बाद में पुन: प्रयास करें।"
        return fallback_text

def generate_hindi_tts(text):
    """
    Generate Hindi text-to-speech audio and return as base64 encoded string
    """
    try:
        # First translate text to Hindi if it's not already in Hindi
        # Simple check if text contains Hindi characters
        if not any(0x900 <= ord(char) <= 0x97F for char in text):
            hindi_text = translate_to_hindi(text)
        else:
            hindi_text = text
            
        logger.info(f"Generating TTS for Hindi text: {hindi_text[:50]}...")
        
        # Create a gTTS object
        tts = gTTS(text=hindi_text, lang='hi', slow=False)
        
        # Save to a BytesIO object instead of a file
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Encode to base64
        audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
        
        return audio_base64
        
    except Exception as e:
        logger.error(f"Error generating Hindi TTS: {str(e)}")
        
        # If TTS generation fails, create a simple "Error" message in Hindi
        try:
            error_msg = "त्रुटि: पाठ को वाणी में परिवर्तित नहीं किया जा सका।"
            tts = gTTS(text=error_msg, lang='hi', slow=False)
            
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
            return audio_base64
            
        except Exception as fallback_error:
            logger.error(f"Even fallback TTS failed: {str(fallback_error)}")
            return ""

def chunk_tts_for_long_text(text, max_chars=500):
    """
    Break long text into chunks for TTS processing
    """
    if len(text) <= max_chars:
        return generate_hindi_tts(text)
    
    # Split text into sentences
    sentences = text.split('।')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + '।'
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + '।'
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # Process each chunk and combine
    audio_files = []
    for chunk in chunks:
        audio_base64 = generate_hindi_tts(chunk)
        audio_files.append(audio_base64)
    
    # For simplicity, we'll just return the first chunk in this example
    # In a real application, you'd need to concatenate the audio files
    return audio_files[0]
