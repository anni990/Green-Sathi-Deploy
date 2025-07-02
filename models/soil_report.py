import os
import pytesseract
from PIL import Image
import pdf2image
import cv2
import numpy as np
import json
import joblib
import pandas as pd
from dotenv import load_dotenv
import tempfile
import zipfile
import mimetypes
import requests
from io import BytesIO

load_dotenv()

# Ensure pytesseract path is set
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')

# Load the model
MODEL_PATH = os.path.join('models', 'crop_prediction_lightgbm new.pkl')

POPPLER_PATH = r'C:\poppler-24.08.0\Library\bin'
# Path to crop varieties JSON file
# CROP_VARIETIES_PATH = os.path.join('data', 'crop_varieties.json')
CROP_VARIETY_PATH = os.path.join('data', 'crop variety.json')

# Define acceptable file formats and their conversion methods
ACCEPTED_FORMATS = {
    # Images
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/bmp': 'image',
    'image/tiff': 'image',
    'image/webp': 'image',
    # Documents
    'application/pdf': 'pdf',
    'application/msword': 'doc',  # .doc
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',  # .docx
    'application/vnd.ms-excel': 'xls',  # .xls
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',  # .xlsx
}

def convert_file_to_image(file_path):
    """
    Convert various file formats to an image that can be processed
    
    Args:
        file_path: Path to the input file
        
    Returns:
        tuple: (success, result) where result is either the image numpy array or error message
               If success is False, the result contains an error message
    """
    try:
        # Get file extension and determine file type
        file_ext = os.path.splitext(file_path)[1].lower()
        mime_type = mimetypes.guess_type(file_path)[0]
        
        # If mime type is not recognized, fall back to extension
        if mime_type not in ACCEPTED_FORMATS:
            if file_ext == '.pdf':
                format_type = 'pdf'
            elif file_ext in ['.doc', '.docx']:
                format_type = 'doc'
            elif file_ext in ['.xls', '.xlsx']:
                format_type = 'xls'
            else:
                # Assume it's an image
                format_type = 'image'
        else:
            format_type = ACCEPTED_FORMATS[mime_type]
        
        # Handle based on format type
        if format_type == 'image':
            # Just load the image
            img = Image.open(file_path)
            
            # Convert from RGBA to RGB if needed
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            
            return True, np.array(img)
            
        elif format_type == 'pdf':
            # Check if PDF has multiple pages
            try:
                pages = pdf2image.convert_from_path(file_path, poppler_path=POPPLER_PATH)
                
                if len(pages) > 1:
                    return False, "The PDF contains multiple pages. Please upload only a single-page soil report."
                
                if not pages:
                    return False, "The PDF appears to be empty."
                
                return True, np.array(pages[0])
            except Exception as e:
                return False, f"Error converting PDF: {str(e)}"
            
        elif format_type in ['doc', 'docx']:
            # Convert to PDF using a web service
            try:
                # This is a stub - production code would use a document conversion service
                # or library like python-docx and then render to an image
                # For now, we'll just return an error
                return False, "Word document conversion is not yet implemented. Please upload an image or PDF."
            except Exception as e:
                return False, f"Error converting Word document: {str(e)}"
                
        elif format_type in ['xls', 'xlsx']:
            # Convert Excel to image
            return False, "Excel file conversion is not yet implemented. Please upload an image or PDF."
        
        else:
            return False, f"Unsupported file format: {file_ext}. Please upload a PDF or image file."
            
    except Exception as e:
        return False, f"Error processing file: {str(e)}"

def get_crop_varieties(crop_name):
    """
    Get detailed information about top 3 varieties of the predicted crop from the JSON file
    
    Args:
        crop_name: The name of the predicted crop
        
    Returns:
        dict: Information about top 3 crop varieties with detailed growing information
    """
    try:
        # Load the crop variety data from the new file
        if os.path.exists(CROP_VARIETY_PATH):
            with open(CROP_VARIETY_PATH, 'r', encoding='utf-8') as f:
                crop_data = json.load(f)
            
            # Find matching varieties for the crop
            crop_name_lower = crop_name.lower()
            matching_varieties = []
            
            # Look for matching varieties
            for variety in crop_data:
                if variety["Crop"].lower() == crop_name_lower:
                    matching_varieties.append(variety)
            
            # Sort by yield (higher is better) and take top 3
            if matching_varieties:
                # Convert yield to numeric if possible for sorting
                for var in matching_varieties:
                    if isinstance(var["Yield (q/acre)"], str):
                        try:
                            # Handle range values like "10–12" by taking the higher value
                            if "–" in var["Yield (q/acre)"]:
                                var["_yield_sort"] = float(var["Yield (q/acre)"].split("–")[1])
                            else:
                                var["_yield_sort"] = float(var["Yield (q/acre)"])
                        except (ValueError, IndexError):
                            var["_yield_sort"] = 0
                    else:
                        var["_yield_sort"] = float(var["Yield (q/acre)"])
                
                # Sort by yield (descending)
                matching_varieties.sort(key=lambda x: x.get("_yield_sort", 0), reverse=True)
                
                # Take top 3 or all if fewer than 3
                top_varieties = matching_varieties[:min(3, len(matching_varieties))]
                
                # Format data for attractive display
                formatted_varieties = []
                for var in top_varieties:
                    formatted_var = {
                        "variety_name": var["Variety"],
                        "maturity_days": var["Maturity (Days)"],
                        "yield": var["Yield (q/acre)"],
                        "key_traits": var["Key Traits"],
                        "soil_requirements": var["Soil Requirements"],
                        "ph": var["ph"],
                        "sowing_time": var["showing time"],
                        "harvesting_time": var["harvesting time"],
                        "irrigation_schedule": var["irrigation schedule"],
                        "seed_rate": var["seed rate and showing"],
                        "fertilizer": {
                            "unirrigated": var["unirrigated showing"],
                            "irrigated_early": var["Irrigated Early Sowing"],
                            "irrigated_late": var["Irrigated Late Sowing"]
                        }
                    }
                    formatted_varieties.append(formatted_var)
                
                return {
                    "crop_name": crop_name,
                    "varieties": formatted_varieties,
                    "found": True
                }
            
            # If no exact match found, try partial matching
            partial_matches = []
            for variety in crop_data:
                crop_var = variety["Crop"].lower()
                if crop_name_lower in crop_var or crop_var in crop_name_lower:
                    partial_matches.append(variety)
            
            if partial_matches:
                # Sort and format same as above
                for var in partial_matches:
                    if isinstance(var["Yield (q/acre)"], str):
                        try:
                            if "–" in var["Yield (q/acre)"]:
                                var["_yield_sort"] = float(var["Yield (q/acre)"].split("–")[1])
                            else:
                                var["_yield_sort"] = float(var["Yield (q/acre)"])
                        except (ValueError, IndexError):
                            var["_yield_sort"] = 0
                    else:
                        var["_yield_sort"] = float(var["Yield (q/acre)"])
                
                partial_matches.sort(key=lambda x: x.get("_yield_sort", 0), reverse=True)
                top_varieties = partial_matches[:min(3, len(partial_matches))]
                
                formatted_varieties = []
                for var in top_varieties:
                    formatted_var = {
                        "variety_name": var["Variety"],
                        "maturity_days": var["Maturity (Days)"],
                        "yield": var["Yield (q/acre)"],
                        "key_traits": var["Key Traits"],
                        "soil_requirements": var["Soil Requirements"],
                        "ph": var["ph"],
                        "sowing_time": var["showing time"],
                        "harvesting_time": var["harvesting time"],
                        "irrigation_schedule": var["irrigation schedule"],
                        "seed_rate": var["seed rate and showing"],
                        "fertilizer": {
                            "unirrigated": var["unirrigated showing"],
                            "irrigated_early": var["Irrigated Early Sowing"],
                            "irrigated_late": var["Irrigated Late Sowing"]
                        }
                    }
                    formatted_varieties.append(formatted_var)
                
                return {
                    "crop_name": crop_name,
                    "varieties": formatted_varieties,
                    "found": True
                }
        
        # If no match found or file doesn't exist, use the old implementation as fallback
        return {
            "crop_name": crop_name,
            "varieties": [
                {
                    "variety_name": "Generic Variety",
                    "maturity_days": "Varies by region",
                    "yield": "Varies by conditions",
                    "key_traits": "Consult local agricultural experts",
                    "soil_requirements": "Depends on specific variety",
                    "ph": "6.0-7.5 (typical range)",
                    "sowing_time": "Season dependent",
                    "harvesting_time": "After maturity",
                    "irrigation_schedule": "As needed",
                    "seed_rate": "Consult local experts",
                    "fertilizer": {
                        "unirrigated": "Based on soil test",
                        "irrigated_early": "Based on soil test",
                        "irrigated_late": "Based on soil test"
                    }
                }
            ],
            "found": False
        }
    
    except Exception as e:
        print(f"Error getting crop varieties: {e}")
        # Return empty dict on error
        return {
            "crop_name": crop_name,
            "varieties": [],
            "found": False
        }

def predict_crop(distt, state, ph, ec, oc, av_p, av_k, zinc, cu, iron, mn):
    """
    Predicts suitable crop using the LightGBM model
    
    Args:
        distt: District name
        state: State name
        ph: pH value
        ec: Electrical conductivity
        oc: Organic carbon percentage
        av_p: Available phosphorus
        av_k: Available potassium
        zinc: Zinc content
        cu: Copper content
        iron: Iron content
        mn: Manganese content
        
    Returns:
        str: Predicted crop name
    """
    try:
        # Load model pipeline
        print("Loading model...")
        model = joblib.load(MODEL_PATH)

        print("Model loaded successfully")
        
        # Create input DataFrame with exact column names
        input_data = pd.DataFrame([{
            'Distt': distt,
            'State': state,
            'pH(1:2)': float(ph),
            'EC': float(ec),
            '%OC': float(oc),
            'Av P(P2O5)': float(av_p),
            'AvK(K2O)': float(av_k),
            'Zinc': float(zinc),
            'Cu': float(cu),
            'Iron': float(iron),
            'Mn': float(mn)
        }])
        
        print(input_data)

        # Predict the crop
        prediction = model.predict(input_data)

        print(prediction)
        return prediction[0]
        
    except Exception as e:
        print(f"Error predicting crop: {e}")
        return "Wheat"  # Default fallback

def extract_text_from_image(img):
    """Extract text from image using OCR"""
    
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Apply basic image processing to improve OCR
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    
    # Apply OCR
    return pytesseract.image_to_string(thresh)

def process_soil_report(report_path, district, state):
    """
    Process a soil report file and extract key soil parameters
    
    Args:
        report_path: Path to the soil report file (image, PDF, etc.)
        district: District name
        state: State name
        
    Returns:
        dict: Extracted soil data or error message
    """
    try:
        # Use the new file conversion utility
        success, result = convert_file_to_image(report_path)
        
        if not success:
            # If conversion failed, return the error message
            return {
                'error': result,
                'ph': None,
                'ec': None,
                'organic_carbon': None,
                'phosphorus': None,
                'potassium': None,
                'zinc': None,
                'copper': None,
                'iron': None,
                'manganese': None
            }
        
        # result is now the image as a numpy array
        img = result
        
        # Instead of processing the image ourselves, we'll use Gemini API
        # This function is now just a placeholder for the app.py route
        # which handles the actual processing with Gemini
        
        # Return empty data that will be filled by Gemini API
        return {
            'ph': None,
            'ec': None,
            'organic_carbon': None,
            'phosphorus': None,
            'potassium': None,
            'zinc': None,
            'copper': None,
            'iron': None,
            'manganese': None
        }
    
    except Exception as e:
        print(f"Error processing soil report: {e}")
        # Return empty values
        return {
            'error': f"Error processing soil report: {str(e)}",
            'ph': None,
            'ec': None,
            'organic_carbon': None,
            'phosphorus': None,
            'potassium': None,
            'zinc': None,
            'copper': None,
            'iron': None,
            'manganese': None
        }

def generate_fertilizer_recommendations(soil_data):
    """Generate fertilizer recommendations based on soil parameters"""
    
    # Import AdvancedFertilizerRecommender from fertilizer_rec.py
    from models.fertilizer_rec import AdvancedFertilizerRecommender
    import os
    import json
    
    # Create instance of AdvancedFertilizerRecommender
    recommender = AdvancedFertilizerRecommender()
    
    # Map soil_data keys to expected keys in fertilizer_rec.py
    soil_values = {
        'pH': soil_data.get('ph', 7.0),
        'EC': soil_data.get('ec', 0.8),
        'OC': soil_data.get('organic_carbon', 0.5),
        'N': soil_data.get('nitrogen', 250),
        'P': soil_data.get('phosphorus', 15),
        'K': soil_data.get('potassium', 40),
        'Zn': soil_data.get('zinc', 1.0),
        'Cu': soil_data.get('copper', 0.5),
        'Fe': soil_data.get('iron', 4.0),
        'Mn': soil_data.get('manganese', 2.0),
        'S': soil_data.get('sulphur', 20)
    }
    
    # Determine crop to use (use 'Wheat' as default if not provided)
    crop = soil_data.get('predicted_crop', 'Wheat')
    
    # Get farmer name and location if available
    farmer_name = soil_data.get('farmer_name', None)
    location = None
    if 'village' in soil_data and 'district' in soil_data:
        location = f"Village {soil_data['village']}, District {soil_data['district']}"
    
    # Generate full fertilizer report (text format for backward compatibility)
    text_report = recommender.generate_report(
        soil_values=soil_values,
        crop=crop,
        farmer_name=farmer_name,
        location=location
    )
    
    # Generate report in JSON format for better display
    json_report = recommender.generate_report_json(
        soil_values=soil_values,
        crop=crop,
        farmer_name=farmer_name,
        location=location
    )
    
    # Get additional crop data from database.json if available
    crop_data = {}
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        database_path = os.path.join(current_dir, '..', 'data', 'database.json')
        if os.path.exists(database_path):
            with open(database_path, 'r', encoding='utf-8') as file:
                db_data = json.load(file)
            
            # Normalize the key for case-insensitive match
            crop_key = next((key for key in db_data if key.lower() == crop.lower()), None)
            if crop_key:
                crop_data = db_data[crop_key]
    except Exception as e:
        print(f"Error loading crop data from database.json: {e}")
    
    # Return the full report and individual recommendations
    return {
        'full_report': text_report,
        'json_report': json_report,
        'crop_data': crop_data,
        'summary': "Based on soil analysis, recommended fertilizers include: UREA, NPK, MOP, and micronutrient supplements as needed."
    }

def categorize_nutrient(value, thresholds):
    """Categorize nutrient level based on thresholds"""
    if value is None:
        return "Unknown"
        
    very_low, low, medium, high = thresholds
    
    if value < very_low:
        return "Very Low"
    elif value < low:
        return "Low"
    elif value < medium:
        return "Medium"
    elif value < high:
        return "Good"
    else:
        return "High" 
    
