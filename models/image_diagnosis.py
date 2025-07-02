import os
import requests
from dotenv import load_dotenv
from PIL import Image
import numpy as np
import base64
import json

load_dotenv()

# HuggingFace API key
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Language codes for response
LANGUAGE_CODES = {
    'english': 'en',
    'hindi': 'hi',
    'bhojpuri': 'bho',
    'bundelkhandi': 'hi',  # Using Hindi as fallback
    'marathi': 'mr',
    'haryanvi': 'hi'  # Using Hindi as fallback
}

# Plant disease classes (example, would be more extensive in production)
PLANT_DISEASES = {
    0: {"plant": "Apple", "disease": "Apple Scab", "recommendation": "Apply fungicide spray specifically designed for apple scab. Remove and destroy infected leaves."},
    1: {"plant": "Apple", "disease": "Black Rot", "recommendation": "Prune infected branches and remove mummified fruits. Apply appropriate fungicides during growing season."},
    2: {"plant": "Apple", "disease": "Cedar Apple Rust", "recommendation": "Separate apple trees from cedar trees if possible. Use fungicide spray designed for rust diseases."},
    3: {"plant": "Apple", "disease": "Healthy", "recommendation": "Your apple plant appears healthy. Continue with regular care and monitoring."},
    4: {"plant": "Corn (Maize)", "disease": "Gray Leaf Spot", "recommendation": "Practice crop rotation. Consider fungicide application if infection is severe."},
    5: {"plant": "Corn (Maize)", "disease": "Common Rust", "recommendation": "Use rust-resistant corn varieties. Apply fungicide early when symptoms first appear."},
    6: {"plant": "Corn (Maize)", "disease": "Northern Leaf Blight", "recommendation": "Rotate crops and implement proper field sanitation. Apply appropriate fungicide if necessary."},
    7: {"plant": "Corn (Maize)", "disease": "Healthy", "recommendation": "Your corn appears healthy. Continue with regular fertilization and water management."},
    8: {"plant": "Tomato", "disease": "Early Blight", "recommendation": "Remove infected leaves immediately. Avoid wetting leaves when watering. Apply fungicide if needed."},
    9: {"plant": "Tomato", "disease": "Late Blight", "recommendation": "Act quickly as this disease spreads rapidly. Apply copper-based fungicide. Consider removing severely infected plants."},
    10: {"plant": "Tomato", "disease": "Leaf Mold", "recommendation": "Improve air circulation around plants. Reduce humidity in greenhouses. Apply suitable fungicide."},
    11: {"plant": "Rice", "disease": "Brown Spot", "recommendation": "Ensure balanced nutrition especially potassium. Use disease-free seeds. Apply fungicide at early signs."},
    12: {"plant": "Rice", "disease": "Blast", "recommendation": "Use resistant varieties. Avoid excess nitrogen. Apply recommended fungicides at heading stage."},
    13: {"plant": "Wheat", "disease": "Brown Rust", "recommendation": "Use resistant wheat varieties. Apply fungicide at flag leaf stage. Rotate crops with non-cereals."},
    14: {"plant": "Wheat", "disease": "Yellow Rust", "recommendation": "Apply fungicide at first sign of disease. Use resistant varieties for future planting."},
    15: {"plant": "Potato", "disease": "Late Blight", "recommendation": "Apply fungicide preventatively. Ensure good air flow by proper spacing. Remove infected plants immediately."},
    16: {"plant": "Potato", "disease": "Early Blight", "recommendation": "Remove bottom leaves that are infected. Apply appropriate fungicide. Maintain consistent soil moisture."},
    17: {"plant": "Tomato", "disease": "Healthy", "recommendation": "Your tomato plant appears healthy. Continue with regular watering and feeding."}
}

def analyze_plant_image(image_path, language='english'):
    """
    Analyze a plant image to detect diseases using HuggingFace API or local model
    
    Args:
        image_path: Path to the image file
        language: Language for the response (default: english)
    
    Returns:
        dict: Analysis results including plant type, disease, confidence, and recommendations
    """
    try:
        # If HuggingFace API key is available, use that
        if OPENROUTER_API_KEY:
            return analyze_with_openrouter(image_path, language)
        else:
            # Fallback to demo/mock results
            return analyze_demo(image_path, language)
            
    except Exception as e:
        print(f"Error analyzing plant image: {e}")
        
        # Prepare error message in the selected language
        if language == 'hindi' or language in ['bundelkhandi', 'haryanvi']:
            error_message = "छवि प्रसंस्करण में त्रुटि हुई। कृपया पौधे की एक और स्पष्ट छवि के साथ पुनः प्रयास करें।"
        elif language == 'bhojpuri':
            error_message = "छवि के प्रोसेसिंग में गड़बड़ी भइल। कृपया पौधा के एगो अउर साफ छवि के साथे फेर से कोशिश करीं।"
        elif language == 'marathi':
            error_message = "प्रतिमा प्रक्रिया करताना त्रुटी आली. कृपया वनस्पतीच्या अधिक स्पष्ट प्रतिमेसह पुन्हा प्रयत्न करा."
        else:
            error_message = "Could not process the image. Please try again with a clearer image of the plant."
            
        return {
            "plant_type": "Unknown",
            "disease": "Identification Failed",
            "confidence": 0.0,
            "recommendation": error_message
        }

def analyze_with_openrouter(image_path, language='english'):
    """Use Gemini Vision API via OpenRouter to analyze the plant image in the specified language"""

    # ✅ Read image and encode in base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Prepare language-specific prompts
    lang_code = LANGUAGE_CODES.get(language, 'en')
    
    # Language-specific instructions
    instructions = {
        'en': (
            "You are a plant disease classifier.\n"
            "Analyze the uploaded image and respond in this JSON format:\n"
            "{\n"
            "  \"plant_type\": \"<plant type>\",\n"
            "  \"disease\": \"<disease name>\",\n"
            "  \"confidence\": <confidence in decimal>,\n"
            "  \"recommendation\": \"<brief advice in English>\"\n"
            "}\n"
            "If unsure, say plant_type='Unknown', disease='Uncertain', confidence=0.0"
            "Please response should be in json format (only provide data no other text) and in english"
        ),
        'hi': (
            "आप एक पौधा रोग वर्गीकरणकर्ता हैं।\n"
            "अपलोड की गई छवि का विश्लेषण करें और इस JSON प्रारूप में उत्तर दें:\n"
            "{\n"
            "  \"plant_type\": \"<पौधे का प्रकार>\",\n"
            "  \"disease\": \"<रोग का नाम>\",\n"
            "  \"confidence\": <दशमलव में विश्वास>\",\n"
            "  \"recommendation\": \"<हिंदी में संक्षिप्त सलाह>\"\n"
            "}\n"
            "यदि अनिश्चित हैं, तो plant_type='अज्ञात', disease='अनिश्चित', confidence=0.0 कहें"
            "Please response should be in json format (only provide data no other text) and in hindi"
        ),
        'bho': (
            "आप एगो पौधा रोग वर्गीकरणकर्ता हईं।\n"
            "अपलोड कइल गइल छवि के विश्लेषण करीं आउर ई JSON प्रारूप में जवाब दीं:\n"
            "{\n"
            "  \"plant_type\": \"<पौधा के किसिम>\",\n"
            "  \"disease\": \"<रोग के नाम>\",\n"
            "  \"confidence\": <दशमलव में विश्वास>\",\n"
            "  \"recommendation\": \"<भोजपुरी में संक्षिप्त सलाह>\"\n"
            "}\n"
            "अगर पक्का नइखीं, त plant_type='अज्ञात', disease='अनिश्चित', confidence=0.0 कहीं"
            "Please response should be in json format (only provide data no other text) and in bhojpuri"
        ),
        'mr': (
            "आपण एक वनस्पती रोग वर्गीकरणकर्ता आहात.\n"
            "अपलोड केलेल्या प्रतिमेचे विश्लेषण करा आणि या JSON स्वरूपात प्रतिसाद द्या:\n"
            "{\n"
            "  \"plant_type\": \"<वनस्पती प्रकार>\",\n"
            "  \"disease\": \"<रोगाचे नाव>\",\n"
            "  \"confidence\": <दशांश मध्ये विश्वास>\",\n"
            "  \"recommendation\": \"<मराठीत संक्षिप्त सल्ला>\"\n"
            "}\n"
            "अनिश्चित असल्यास, plant_type='अज्ञात', disease='अनिश्चित', confidence=0.0 असे म्हणा"
            "Please response should be in json format (only provide data no other text) and in marathi"
        )
    }
    
    # Default to Hindi for languages without specific translations
    if lang_code not in instructions:
        lang_code = 'hi' if lang_code in ['bho', 'mr'] else 'en'
    
    instruction_text = instructions.get(lang_code, instructions['en'])

    # ✅ Compose the prompt
    prompt = {
        "model": "meta-llama/llama-4-maverick:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": instruction_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",  # 🔑 Replace with your key
        "Content-Type": "application/json"
    }

    # ✅ Make the POST request
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=prompt, headers=headers)

    print(response.text)
    print(response.status_code)

    # ✅ Error handling
    if response.status_code != 200:
        print(f"API Error: {response.status_code} - {response.text}")
        raise Exception("Failed to fetch prediction from Gemini via OpenRouter.")

    response_data = response.json()

    try:
        message = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        message = message.replace("```json", "").replace("```", "").replace("\n", "")
        print("Gemini Response:\n", message)

        # ✅ Parse the response assuming it's JSON-like
        try:
            result = json.loads(message)
        except json.JSONDecodeError:
            print("Message is not in JSON format.")
            result = None

        # Prepare default messages based on language
        default_unknown = "Unknown"
        default_uncertain = "Uncertain"
        default_recommendation = "The analysis was inconclusive. Please try with a clearer image or consult a local agricultural expert."
        
        if language == 'hindi' or language in ['bundelkhandi', 'haryanvi']:
            default_unknown = "अज्ञात"
            default_uncertain = "अनिश्चित"
            default_recommendation = "विश्लेषण अनिर्णायक था। कृपया एक स्पष्ट छवि के साथ पुनः प्रयास करें या स्थानीय कृषि विशेषज्ञ से परामर्श करें।"
        elif language == 'bhojpuri':
            default_unknown = "अज्ञात"
            default_uncertain = "अनिश्चित"
            default_recommendation = "विश्लेषण अनिर्णायक रहल। कृपया एगो साफ छवि के साथे फेर से कोशिश करीं या स्थानीय कृषि विशेषज्ञ से सलाह लीं।"
        elif language == 'marathi':
            default_unknown = "अज्ञात"
            default_uncertain = "अनिश्चित"
            default_recommendation = "विश्लेषण अनिश्चित होते. कृपया अधिक स्पष्ट प्रतिमेसह पुन्हा प्रयत्न करा किंवा स्थानिक कृषी तज्ञांचा सल्ला घ्या."

        return {
            "plant_type": result.get("plant_type", default_unknown),
            "disease": result.get("disease", default_uncertain),
            "confidence": result.get("confidence", 0.0),
            "recommendation": result.get("recommendation", default_recommendation)
        }

    except Exception as e:
        print(f"Response parsing error: {e}")
        
        # Language-specific error messages
        if language == 'hindi' or language in ['bundelkhandi', 'haryanvi']:
            error_msg = "विश्लेषण अनिर्णायक था। कृपया एक स्पष्ट छवि के साथ पुनः प्रयास करें या स्थानीय कृषि विशेषज्ञ से परामर्श करें।"
        elif language == 'bhojpuri':
            error_msg = "विश्लेषण अनिर्णायक रहल। कृपया एगो साफ छवि के साथे फेर से कोशिश करीं या स्थानीय कृषि विशेषज्ञ से सलाह लीं।"
        elif language == 'marathi':
            error_msg = "विश्लेषण अनिश्चित होते. कृपया अधिक स्पष्ट प्रतिमेसह पुन्हा प्रयत्न करा किंवा स्थानिक कृषी तज्ञांचा सल्ला घ्या."
        else:
            error_msg = "The analysis was inconclusive. Please try with a clearer image or consult a local agricultural expert."
        
        return {
            "plant_type": default_unknown,
            "disease": default_uncertain,
            "confidence": 0.0,
            "recommendation": error_msg
        }
    

def analyze_demo(image_path, language='english'):
    """Provide a demo/mock analysis when no API key is available"""
    
    # Simulate a model prediction by using basic image properties
    image = Image.open(image_path).convert('RGB')
    
    # Calculate average color values as a very basic feature
    img_array = np.array(image)
    avg_color = np.mean(img_array, axis=(0, 1))
    
    # Use the color to deterministically select a "class"
    # This is just for demonstration and would be replaced by actual model inference
    color_sum = sum(avg_color)
    class_id = int(color_sum % len(PLANT_DISEASES))
    
    # Get the corresponding disease info
    result = PLANT_DISEASES[class_id]
    
    # Calculate a mock confidence score (0.7-0.95 range)
    confidence = 0.7 + ((color_sum % 25) / 100)
    
    # Translate for non-English languages
    recommendation = result["recommendation"]
    
    if language == 'hindi' or language in ['bundelkhandi', 'haryanvi']:
        # Very simplified translation for demo purposes
        if "healthy" in result["disease"].lower():
            recommendation = f"आपका {result['plant']} स्वस्थ दिखता है। नियमित देखभाल जारी रखें।"
        else:
            recommendation = f"इस रोग के लिए उपयुक्त कवकनाशी का छिड़काव करें और प्रभावित पत्तियों को हटा दें।"
    elif language == 'bhojpuri':
        if "healthy" in result["disease"].lower():
            recommendation = f"रउआ के {result['plant']} स्वस्थ लागत बा। नियमित देखभाल जारी रखीं।"
        else:
            recommendation = f"ई रोग खातिर उपयुक्त कवकनाशी के छिड़काव करीं आउर प्रभावित पत्ती के हटा दीं।"
    elif language == 'marathi':
        if "healthy" in result["disease"].lower():
            recommendation = f"तुमचे {result['plant']} निरोगी दिसत आहे. नियमित काळजी चालू ठेवा."
        else:
            recommendation = f"या रोगासाठी योग्य बुरशीनाशक फवारा आणि प्रभावित पाने काढून टाका."
    
    return {
        "plant_type": result["plant"],
        "disease": result["disease"],
        "confidence": confidence,
        "recommendation": recommendation
    } 