import os
import requests
from dotenv import load_dotenv
import json
import re
import unicodedata
from datetime import datetime
import uuid
from .database import db

load_dotenv()

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    language = db.Column(db.String(20), default='hindi')
    messages = db.relationship('ChatMessage', backref='chat_session', lazy=True, cascade='all, delete-orphan')

class ChatMessage(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    input_type = db.Column(db.String(20), default='text')  # 'text', 'voice', 'image', 'soil_report'

class PlantImage(db.Model):
    __tablename__ = 'plant_images'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    chat_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)  # Path to the stored image
    plant_type = db.Column(db.String(100), nullable=True)
    disease = db.Column(db.String(100), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SoilReport(db.Model):
    __tablename__ = 'soil_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    chat_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    report_path = db.Column(db.String(255), nullable=False)  # Path to the stored report
    district = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    soil_type = db.Column(db.String(100), nullable=True)
    ph_value = db.Column(db.Float, nullable=True)
    ec = db.Column(db.Float, nullable=True)
    organic_carbon = db.Column(db.Float, nullable=True)
    phosphorus = db.Column(db.Float, nullable=True)
    potassium = db.Column(db.Float, nullable=True)
    zinc = db.Column(db.Float, nullable=True)
    copper = db.Column(db.Float, nullable=True)
    iron = db.Column(db.Float, nullable=True)
    manganese = db.Column(db.Float, nullable=True)
    nitrogen = db.Column(db.Float, nullable=True)
    sulphur = db.Column(db.Float, nullable=True)
    predicted_crop = db.Column(db.String(100), nullable=True)
    crop_recommendations = db.Column(db.Text, nullable=True)
    fertilizer_recommendations = db.Column(db.Text, nullable=True)
    full_fertilizer_report = db.Column(db.Text, nullable=True)
    json_fertilizer_report = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Configure API keys
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Dictionary of language codes
LANGUAGE_CODES = {
    'english': 'en',
    'hindi': 'hi',
    'bhojpuri': 'bho',
    'bundelkhandi': 'hi',  # Using Hindi as fallback
    'marathi': 'mr',
    'haryanvi': 'hi',  # Using Hindi as fallback
    'bengali': 'bn',
    'tamil': 'ta',
    'telugu': 'te',
    'kannada': 'kn',
    'gujarati': 'gu',
    'urdu': 'ur',
    'malayalam': 'ml',
    'punjabi': 'pa'
}

# Language display names
LANGUAGE_NAMES = {
    'english': 'English',
    'hindi': 'Hindi/हिंदी',
    'bhojpuri': 'Bhojpuri/भोजपुरी',
    'bundelkhandi': 'Bundelkhandi/बुंदेलखंडी',
    'marathi': 'Marathi/मराठी',
    'haryanvi': 'Haryanvi/हरियाणवी',
    'bengali': 'Bengali/বাংলা',
    'tamil': 'Tamil/தமிழ்',
    'telugu': 'Telugu/తెలుగు',
    'kannada': 'Kannada/ಕನ್ನಡ',
    'gujarati': 'Gujarati/ગુજરાતી',
    'urdu': 'Urdu/اردو',
    'malayalam': 'Malayalam/മലയാളം',
    'punjabi': 'Punjabi/ਪੰਜਾਬੀ'
}

# Error messages for different languages
ERROR_MESSAGES = {
    'english': "I'm sorry, I encountered an error. Please try again.",
    'hindi': "मुझे खेद है, मुझे एक त्रुटि मिली। कृपया पुनः प्रयास करें।",
    'bengali': "দুঃখিত, একটি ত্রুটি হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
    'marathi': "मला माफ करा, मला एक त्रुटी आली. कृपया पुन्हा प्रयत्न करा.",
    'tamil': "மன்னிக்கவும், ஒரு பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.",
    'telugu': "క్షమించండి, నాకు ఒక లోపం వచ్చింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    'kannada': "ಕ್ಷಮಿಸಿ, ನನಗೆ ದೋಷ ಎದುರಾಯಿತು. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    'gujarati': "માફ કરશો, મને એક ભૂલ મળી. કૃપા કરીને ફરીથી પ્રયાસ કરો.",
    'urdu': "معذرت، مجھے ایک خرابی ملی۔ براہ کرم دوبارہ کوشش کریں۔",
    'malayalam': "ക്ഷമിക്കണം, എനിക്ക് ഒരു പിശക് സംഭവിച്ചു. ദയവായി വീണ്ടും ശ്രമിക്കുക.",
    'punjabi': "ਮੈਨੂੰ ਮਾਫ਼ ਕਰਨਾ, ਮੈਨੂੰ ਇੱਕ ਗਲਤੀ ਮਿਲੀ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
    'bhojpuri': "हमका माफ करीं, हमका एगो त्रुटि मिलल। कृपया फेर से कोशिश करीं।",
    'bundelkhandi': "हमें माफ करें, हमें एक त्रुटि मिली। कृपया फिर से कोशिश करें।",
    'haryanvi': "म्हाफ करियो, म्हनै एक गलती मिली। दुबारा कोशिश करो।"
}

# Preprocess text to handle special characters
def preprocess_text(text):
    """Clean text to prevent tokenizer vocabulary errors"""
    if not text:
        return ""
        
    # Normalize Unicode characters
    text = unicodedata.normalize('NFKC', text)
    
    # Replace problematic characters with their Unicode equivalents
    replacements = {
        '/': '∕',  # Division slash
        '\\': '∕',  # Division slash
        '*': '∗',   # Asterisk operator
        '•': '●',   # Bullet
        '`': '´'    # Acute accent
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Preserve markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'**\1**', text)  # Preserve bold
    text = re.sub(r'\*(.*?)\*', r'*\1*', text)        # Preserve italic
    text = re.sub(r'`(.*?)`', r'`\1`', text)          # Preserve code
    
    # Clean up extra spaces while preserving newlines
    text = re.sub(r'[^\S\r\n]+', ' ', text)  # Replace multiple spaces with single space
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Replace multiple newlines with double newline
    
    return text.strip()

# Using OpenRouter API for models
def process_text_query(query, language='hindi'):
    """
    Process a text query in the specified language and return a response.
    
    Args:
        query: The text input from the user
        language: The language code (english, hindi, etc.)
    
    Returns:
        str: Response in the same language as the input
    """
    try:
        # Clean user input
        clean_query = preprocess_text(query)
        
        # If we're using OpenRouter
        if OPENROUTER_API_KEY:
            try:
                response = process_with_openrouter(clean_query, language)
                print(response)
                return preprocess_text(response)
            except Exception as api_error:
                print(f"OpenRouter API error: {api_error}")
                # Try with HuggingFace if OpenRouter fails
                if HUGGINGFACE_API_KEY:
                    try:
                        response = process_with_huggingface(clean_query, language)
                        return preprocess_text(response)
                    except Exception as hf_error:
                        print(f"HuggingFace API error: {hf_error}")
                        # Fall back to demo response if both APIs fail
                        response = demo_response(clean_query, language)
                        return preprocess_text(response)
                else:
                    # Fall back to demo response if HuggingFace not available
                    response = demo_response(clean_query, language)
                    return preprocess_text(response)
        # Fallback to HuggingFace
        elif HUGGINGFACE_API_KEY:
            try:
                response = process_with_huggingface(clean_query, language)
                return preprocess_text(response)
            except Exception as hf_error:
                print(f"HuggingFace API error: {hf_error}")
                # Fall back to demo response if HuggingFace fails
                response = demo_response(clean_query, language)
                return preprocess_text(response)
        # Local fallback for demo
        else:
            response = demo_response(clean_query, language)
            return preprocess_text(response)
    
    except Exception as e:
        print(f"Critical error processing text query: {e}")
        # Return a simple message in the appropriate language
        if language in ERROR_MESSAGES:
            return ERROR_MESSAGES[language]
        else:
            return ERROR_MESSAGES['english']

def process_with_openrouter(query, language):
    """Use OpenRouter API to process the query"""
    
    # Get language display name for clearer instructions
    language_display = LANGUAGE_NAMES.get(language, language)
    
    # Define a system prompt based on language
    if language == 'english':
        system_prompt = f"You are an AI agricultural assistant named 'AI ग्रीन साथी' helping farmers. Answer questions concisely and clearly in English only. Provide practical advice for farming problems."
    else:  # Other Indian languages
        system_prompt = f"आप 'AI ग्रीन साथी' नाम के एक AI कृषि सहायक हैं जो किसानों की मदद कर रहे हैं। प्रश्नों का उत्तर केवल {language_display} भाषा में संक्षेप में और स्पष्ट रूप से दें। खेती की समस्याओं के लिए व्यावहारिक सलाह प्रदान करें। अपने उत्तर में अंग्रेजी का प्रयोग न करें।"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    # List of models to try in order of preference
    models = [
        "google/gemma-3-27b-it:free",
        "google/gemma-2-9b-it:free",
        "google/gemma-3-2b-it:free",
        "mistralai/mistral-7b-instruct:free",
        "openchat/openchat-3.5:free"
    ]
    
    # Try each model in sequence if we encounter rate limits
    last_error = None
    
    for model in models:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                    {"role": "system", "content": f"Remember to answer only in {language_display}. Do not use any other language."}
                ],
                "max_tokens": 500,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=30  # Add timeout to prevent hanging
            )
            
            # Check for rate limit errors (HTTP 429)
            if response.status_code == 429:
                print(f"Rate limit reached for model {model}, trying next model...")
                last_error = response.text
                continue  # Try the next model
                
            response_data = response.json()
            
            if response.status_code == 200 and "choices" in response_data:
                print(f"Successfully used model: {model}")
                return response_data["choices"][0]["message"]["content"]
            else:
                last_error = response.text
                print(f"Error with model {model}: {last_error}")
                # Try the next model
        except Exception as e:
            last_error = str(e)
            print(f"Exception with model {model}: {last_error}")
            # Continue to the next model
    
    # If we've exhausted all models, raise the last error
    raise Exception(f"All OpenRouter models failed. Last error: {last_error}")

def process_with_huggingface(query, language):
    """Use HuggingFace API to process the query"""
    
    lang_code = LANGUAGE_CODES.get(language, 'en')
    language_display = LANGUAGE_NAMES.get(language, language)
    
    # List of models to try in order of preference - these are lightweight and usually available
    models = [
        "google/mt5-base",
        "google/flan-t5-small",
        "microsoft/phi-2",
        "facebook/bart-large-cnn",
        "gpt2"
    ]
    
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    # Create a more specific prompt with explicit language instruction
    prompt = f"Answer this agricultural question in {language_display} language only. Do not use any other language in your response: {query}"
    
    # Try each model in sequence if we encounter errors
    last_error = None
    
    for model_name in models:
        try:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 500,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True,
                    "early_stopping": True
                }
            }
            
            api_url = f"https://api-inference.huggingface.co/models/{model_name}"
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 401 or response.status_code == 403:
                # Auth or permission error, try next model
                last_error = response.text
                print(f"Permission error with model {model_name}: {last_error}")
                continue
                
            if response.status_code == 200:
                print(f"Successfully used HuggingFace model: {model_name}")
                return response.json()[0]["generated_text"]
            else:
                last_error = response.text
                print(f"Error with HuggingFace model {model_name}: {last_error}")
                # Try the next model
        except Exception as e:
            last_error = str(e)
            print(f"Exception with HuggingFace model {model_name}: {last_error}")
            # Continue to the next model
    
    # If we've exhausted all models, raise the last error
    raise Exception(f"All HuggingFace models failed. Last error: {last_error}")

def demo_response(query, language):
    """
    Provide a demo response when no API keys are available or when API calls fail
    
    In a production environment, you would use the actual AI models.
    """
    
    # Simple keyword matching for demo purposes
    query_lower = query.lower()
    
    # English responses
    if language == 'english':
        if any(word in query_lower for word in ['weather', 'rain', 'forecast']):
            return "I recommend checking the local meteorological department website for the most accurate weather forecast in your area."
        elif any(word in query_lower for word in ['fertilizer', 'fertiliser', 'nutrients']):
            return "For most crops, a balanced NPK fertilizer works well. Consider getting a soil test to know exactly what your soil needs."
        elif any(word in query_lower for word in ['pest', 'insect', 'disease']):
            return "First identify the pest or disease. For organic control, try neem oil or beneficial insects. Chemical controls should be used carefully following the instructions."
        else:
            return "That's a good agricultural question. For specific advice on this topic, I recommend consulting your local agricultural extension office."
    
    # Hindi responses
    elif language == 'hindi':
        if any(word in query_lower for word in ['weather', 'rain', 'forecast', 'मौसम', 'बारिश', 'पूर्वानुमान']):
            return "मैं आपके क्षेत्र के लिए सबसे सटीक मौसम पूर्वानुमान के लिए स्थानीय मौसम विभाग की वेबसाइट देखने की सलाह देता हूं।"
        elif any(word in query_lower for word in ['fertilizer', 'fertiliser', 'nutrients', 'उर्वरक', 'खाद', 'पोषक']):
            return "अधिकांश फसलों के लिए, एक संतुलित NPK उर्वरक अच्छा काम करता है। यह जानने के लिए कि आपकी मिट्टी को ठीक से क्या चाहिए, मिट्टी का परीक्षण कराएं।"
        elif any(word in query_lower for word in ['pest', 'insect', 'disease', 'कीट', 'कीड़े', 'बीमारी']):
            return "सबसे पहले कीट या रोग की पहचान करें। जैविक नियंत्रण के लिए, नीम का तेल या फायदेमंद कीड़े आजमाएं। रासायनिक नियंत्रण का निर्देशों का पालन करते हुए सावधानी से उपयोग किया जाना चाहिए।"
        else:
            return "यह एक अच्छा कृषि प्रश्न है। इस विषय पर विशिष्ट सलाह के लिए, मैं अपने स्थानीय कृषि विस्तार कार्यालय से परामर्श करने की सलाह देता हूं।"
    
    # Bengali responses
    elif language == 'bengali':
        if any(word in query_lower for word in ['weather', 'rain', 'forecast', 'আবহাওয়া', 'বৃষ্টি']):
            return "আমি আপনার এলাকার সবচেয়ে সঠিক আবহাওয়া পূর্বাভাসের জন্য স্থানীয় আবহাওয়া দপ্তরের ওয়েবসাইট দেখার পরামর্শ দিচ্ছি।"
        elif any(word in query_lower for word in ['fertilizer', 'fertiliser', 'nutrients', 'সার', 'পুষ্টি']):
            return "বেশিরভাগ ফসলের জন্য, একটি ভারসাম্যপূর্ণ NPK সার ভালো কাজ করে। আপনার মাটির ঠিক কী প্রয়োজন তা জানতে মাটি পরীক্ষা করার কথা বিবেচনা করুন।"
        else:
            return "এটি একটি ভালো কৃষি প্রশ্ন। এই বিষয়ে নির্দিষ্ট পরামর্শের জন্য, আমি আপনার স্থানীয় কৃষি বিস্তার অফিসের সাথে পরামর্শ করার সুপারিশ করি।"
            
    # For all other languages, return a generic message
    else:
        # Use language code to determine which language to respond in
        lang_code = LANGUAGE_CODES.get(language, 'en')
        
        if lang_code == 'mr':  # Marathi
            return "ही एक चांगली कृषी संबंधित प्रश्न आहे. या विषयावर अधिक माहितीसाठी, स्थानिक कृषी विभागाशी संपर्क साधावा."
        elif lang_code == 'ta':  # Tamil
            return "இது ஒரு நல்ல விவசாய கேள்வி. இந்த தலைப்பில் குறிப்பிட்ட ஆலோசனைக்கு, உங்கள் உள்ளூர் விவசாய விரிவாக்க அலுவலகத்தை ஆலோசிக்க பரிந்துரைக்கிறேன்."
        elif lang_code == 'te':  # Telugu
            return "ఇది ఒక మంచి వ్యవసాయ ప్రశ్న. ఈ అంశంపై నిర్దిష్ట సలహా కోసం, మీ స్థానిక వ్యవసాయ విస్తరణ కార్యాలయాన్ని సంప్రదించాలని నేను సిఫార్సు చేస్తున్నాను."
        elif lang_code == 'kn':  # Kannada
            return "ಇದು ಒಳ್ಳೆಯ ಕೃಷಿ ಪ್ರಶ್ನೆ. ಈ ವಿಷಯದ ಬಗ್ಗೆ ನಿರ್ದಿಷ್ಟ ಸಲಹೆಗಾಗಿ, ನಿಮ್ಮ ಸ್ಥಳೀಯ ಕೃಷಿ ವಿಸ್ತರಣಾ ಕಚೇರಿಯನ್ನು ಸಂಪರ್ಕಿಸಲು ನಾನು ಸಲಹೆ ನೀಡುತ್ತೇನೆ."
        elif lang_code == 'gu':  # Gujarati
            return "આ એક સારો કૃષિ પ્રશ્ન છે. આ વિષય પર ચોક્કસ સલાહ માટે, હું તમારી સ્થાનિક કૃષિ વિસ્તરણ કચેરીની સલાહ લેવાની ભલામણ કરું છું."
        elif lang_code == 'ur':  # Urdu
            return "یہ ایک اچھا زراعتی سوال ہے۔ اس موضوع پر مخصوص مشورے کے لیے، میں آپ کے مقامی زراعتی توسیع دفتر سے مشورہ کرنے کی سفارش کرتا ہوں۔"
        elif lang_code == 'ml':  # Malayalam
            return "ഇത് ഒരു നല്ല കാർഷിക ചോദ്യമാണ്. ഈ വിഷയത്തിൽ പ്രത്യേക ഉപദേശത്തിനായി, നിങ്ങളുടെ പ്രാദേശിക കാർഷിക വിപുലീകരണ ഓഫീസുമായി ആലോചിക്കാൻ ഞാൻ ശുപാർശ ചെയ്യുന്നു."
        elif lang_code == 'pa':  # Punjabi
            return "ਇਹ ਇੱਕ ਚੰਗਾ ਖੇਤੀਬਾੜੀ ਸਵਾਲ ਹੈ। ਇਸ ਵਿਸ਼ੇ 'ਤੇ ਵਿਸ਼ੇਸ਼ ਸਲਾਹ ਲਈ, ਮੈਂ ਤੁਹਾਡੇ ਸਥਾਨਕ ਖੇਤੀਬਾੜੀ ਵਿਸਤਾਰ ਦਫਤਰ ਨਾਲ ਸਲਾਹ-ਮਸ਼ਵਰਾ ਕਰਨ ਦੀ ਸਿਫਾਰਸ਼ ਕਰਦਾ ਹਾਂ।"
        elif lang_code == 'bho':  # Bhojpuri
            return "ई एगो नीक कृषि प्रश्न हवे। एह विषय पर विशिष्ट सलाह खातिर, हम आपके स्थानीय कृषि प्रसार कार्यालय से परामर्श करे के सलाह देत बानी।"
        else:
            # Default to Hindi for any other language
            return "यह एक अच्छा कृषि प्रश्न है। इस विषय पर विशिष्ट सलाह के लिए, मैं अपने स्थानीय कृषि विस्तार कार्यालय से परामर्श करने की सलाह देता हूं।"

# Function to get welcome message based on language
def get_welcome_message(language):
    """
    Returns a welcome message in the requested language
    
    Args:
        language: The language code or name (english, hindi, etc.)
        
    Returns:
        str: Welcome message in the specified language
    """
    
    welcome_messages = {
        'english': "Hello! I'm your Green Sathi. How can I help you with your farming questions today?",
        'hindi': "नमस्ते! मैं आपका ग्रीन साथी हूँ। आज मैं आपकी खेती संबंधित प्रश्नों में कैसे मदद कर सकता हूँ?",
        'bengali': "নমস্কার! আমি আপনার গ্রীন সাথী। আজ আমি আপনার কৃষি সংক্রান্ত প্রশ্নগুলিতে কীভাবে সাহায্য করতে পারি?",
        'marathi': "नमस्कार! मी तुमचा ग्रीन साथी आहे. आज मी तुम्हाला तुमच्या शेती संबंधित प्रश्नांमध्ये कशी मदत करू शकतो?",
        'tamil': "வணக்கம்! நான் உங்கள் கிரீன் சாதி. இன்று உங்கள் விவசாய கேள்விகளில் நான் எப்படி உதவ முடியும்?",
        'telugu': "నమస్కారం! నేను మీ గ్రీన్ సాథి. నేడు మీ వ్యవసాయ ప్రశ్నలలో నేను మీకు ఎలా సహాయం చేయగలను?",
        'kannada': "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಗ್ರೀನ್ ಸಾಥಿ. ಇಂದು ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳಲ್ಲಿ ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
        'gujarati': "નમસ્તે! હું તમારો ગ્રીન સાથી છું. આજે હું તમારા ખેતી સંબંધੀ પ્રશ્નોમાં કેવી રીતે મદદ કરી શકું છું?",
        'urdu': "سلام! میں آپ کا گرین ساتھی ہوں۔ آج میں آپ کے زرعی سوالات میں کیسے مدد کر سکتا ہوں؟",
        'malayalam': "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ ഗ്രീൻ സാഥി ആണ്. ഇന്ന് നിങ്ങളുടെ കാർഷിക ചോദ്യങ്ങളിൽ എനിക്ക് എങ്ങനെ സഹായിക്കാൻ കഴിയും?",
        'punjabi': "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਗ੍ਰੀਨ ਸਾਥੀ ਹਾਂ। ਅੱਜ ਮੈਂ ਤੁਹਾਡੇ ਖੇਤੀਬਾੜੀ ਸੰਬੰਧੀ ਸਵਾਲਾਂ ਵਿੱਚ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
        'bhojpuri': "नमस्कार! हम आपके ग्रीन साथी हैं। आज हम आपके खेती से जुड़ल सवालन में केही मदद कर सकत बानी?",
        'bundelkhandi': "नमस्कार! हम आपके ग्रीन साथी हैं। आज हम आपके खेती से जुड़े सवालों में कैसे मदद कर सकते हैं?",
        'haryanvi': "नमस्कार! मैं थारा ग्रीन साथी हूँ। आज मैं थारे खेती से जुड़े सवालां में किस तरह मदद कर सकूं?"
    }
    
    # Return the welcome message in the requested language, or default to Hindi if not found
    return welcome_messages.get(language, welcome_messages['hindi']) 