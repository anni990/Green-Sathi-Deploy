import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from dotenv import load_dotenv
import uuid
import logging

# Import model handlers
from models.chat_model import process_text_query, get_welcome_message, db, ChatSession, ChatMessage, PlantImage, SoilReport
from models.speech_handler import speech_to_text, text_to_speech
from models.image_diagnosis import analyze_plant_image
from models.soil_report import process_soil_report, predict_crop, generate_fertilizer_recommendations, get_crop_varieties, convert_file_to_image
from models.fetch_weather import get_location_name, get_weather_condition, get_weather_icon, get_current_humidity, get_current_precipitation, get_hourly_weather_codes, format_time, generate_farming_advice
from models.auction_models import CropForSale, Commodity, District, Bid
from models.user import User as UserModel  # Add this import at the top with other imports

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')

# Configure upload folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folders if they don't exist
os.makedirs(os.path.join(UPLOAD_FOLDER, 'crops'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(
    os.getenv('DB_USER', 'root'),
    os.getenv('DB_PASSWORD', ''),
    os.getenv('DB_HOST', 'localhost'),
    os.getenv('DB_NAME', 'farmers_chatbot')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'voice'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'soil_reports'), exist_ok=True)

# Setup MySQL connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'farmers_chatbot')
    )

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id, username, email, preferred_language, user_role='farmer', latitude=None, longitude=None):
        self.id = id
        self.username = username
        self.email = email
        self.preferred_language = preferred_language
        self.user_role = user_role
        self.latitude = latitude
        self.longitude = longitude

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user_data:
        return User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            preferred_language=user_data['preferred_language'],
            user_role=user_data.get('user_role', 'farmer'),
            latitude=user_data.get('latitude'),
            longitude=user_data.get('longitude')
        )
    return None

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        language = request.form['language']
        user_role = request.form['user_role']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # Check if username or email already exists
        if db.session.query(User).filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
        if db.session.query(User).filter_by(email=email).first():
            flash('Email already registered. Please login or use a different email.', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            preferred_language=language,
            user_role=user_role
        )
        new_user.set_password(password)
        
        # Add location if provided
        if latitude and longitude:
            new_user.latitude = float(latitude)
            new_user.longitude = float(longitude)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            # Update last login
            cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", 
                          (datetime.now(), user_data['id']))
            conn.commit()
            
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                preferred_language=user_data['preferred_language'],
                user_role=user_data.get('user_role', 'farmer'),
                latitude=user_data.get('latitude'),
                longitude=user_data.get('longitude')
            )
            login_user(user)
            cursor.close()
            conn.close()

            # Redirect based on user role
            if user_data.get('user_role') == 'farmer':
                return redirect(url_for('chat'))
            elif user_data.get('user_role') == 'dealer':
                return redirect(url_for('available_crops'))
            else:
                flash('Invalid user role')
                return redirect(url_for('login'))
        
        cursor.close()
        conn.close()
        flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/chat')
@login_required
def chat():
    try:
        chat_id = request.args.get('chat_id')
        language = request.args.get('language', 'hindi')
        
        # Get user_id (0 for non-authenticated users)
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Get all chat sessions for the sidebar - filter by user_id if authenticated
        if user_id:
            chat_history = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
        else:
            # For non-authenticated users, only show chats with no user_id
            chat_history = ChatSession.query.filter_by(user_id=None).order_by(ChatSession.created_at.desc()).all()
        
        # Get messages for the current chat if chat_id is provided
        current_chat = None
        messages = []
        
        if chat_id:
            current_chat = db.session.get(ChatSession, chat_id)
            
            # Security check: Make sure the user can only access their own chats
            if current_chat and current_user.is_authenticated and current_chat.user_id != user_id:
                # If this chat belongs to another user, redirect to a new chat
                return redirect(url_for('chat', language=language))
                
            if current_chat:
                # Update the user_id if it's not set and user is authenticated
                if current_user.is_authenticated and current_chat.user_id is None:
                    current_chat.user_id = user_id
                    db.session.commit()
                    
                messages = ChatMessage.query.filter_by(chat_id=chat_id).order_by(ChatMessage.timestamp).all()
        else:
            # Create a new chat session if none is specified
            try:
                db.session.rollback()  # Roll back any existing transaction
                new_chat = ChatSession(language=language, user_id=user_id)
                db.session.add(new_chat)
                db.session.commit()
                current_chat = new_chat
                chat_id = new_chat.id
                
                # Add a welcome message using the get_welcome_message function
                welcome_text = get_welcome_message(language)
                
                # Get or create system user for bot messages
                system_user_id = get_or_create_system_user()
                
                bot_message = ChatMessage(
                    chat_id=chat_id,
                    text=welcome_text,
                    sender='bot',
                    user_id=system_user_id  # Use system user instead of NULL
                )
                db.session.add(bot_message)
                db.session.commit()
                
                # Get messages for the new chat
                messages = ChatMessage.query.filter_by(chat_id=chat_id).order_by(ChatMessage.timestamp).all()
            except Exception as e:
                db.session.rollback()
                print(f"Error creating new chat: {str(e)}")
                raise
        
        return render_template('chat.html',
                            chat_history=chat_history,
                            current_chat_id=chat_id,
                            messages=messages,
                            language=language)
    except Exception as e:
        import traceback
        print(f"Error in chat route: {str(e)}")
        print(traceback.format_exc())
        # Return a more user-friendly error page
        return render_template('error.html', 
                               error_message="There was a problem loading the chat. Please try again later.",
                               error_details=str(e) if app.debug else None), 500

@app.route('/api/create_chat', methods=['POST'])
@login_required
def create_chat():
    data = request.get_json()
    language = data.get('language', 'hindi')
    
    # Get user_id if authenticated
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Create new chat with UUID-style ID
    new_chat = ChatSession(language=language, user_id=user_id)
    db.session.add(new_chat)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'chat_id': new_chat.id
    })

@app.route('/api/get_chat_history')
@login_required
def get_chat_history():
    # Get user_id if authenticated
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Filter chats by user_id if authenticated
    if user_id:
        chats = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
    else:
        # For non-authenticated users, only show chats with no user_id
        chats = ChatSession.query.filter_by(user_id=None).order_by(ChatSession.created_at.desc()).all()
    
    return jsonify({
        'chats': [{
            'id': chat.id,
            'created_at': chat.created_at.isoformat(),
            'language': chat.language,
            'messages': [{
                'text': msg.text,
                'timestamp': msg.timestamp.isoformat()
            } for msg in chat.messages]
        } for chat in chats]
    })

@app.route('/api/process_text', methods=['POST'])
@login_required
def process_text():
    try:
        data = request.get_json()
        message = data.get('message')
        chat_id = data.get('chat_id')
        language = data.get('language', 'hindi')
        
        # Get user_id if authenticated
        user_id = current_user.id if current_user.is_authenticated else None
        
        if not chat_id:
            return jsonify({'error': 'No chat session specified'}), 400
        
        try:
            # Verify that the chat session exists
            chat_session = db.session.get(ChatSession, chat_id)
            if not chat_session:
                return jsonify({'error': f'Chat session {chat_id} not found'}), 404
            
            # Save user message
            user_message = ChatMessage(
                chat_id=chat_id,
                user_id=user_id,
                text=message,
                sender='user'
            )
            db.session.add(user_message)
            db.session.flush()  # Flush without committing
            
            # Process the message and get response
            response = process_text_query(message, language)
            
            # Get system user id for bot messages
            system_user_id = get_or_create_system_user()
            
            # Save bot response
            bot_message = ChatMessage(
                chat_id=chat_id,
                user_id=system_user_id,  # Use system user instead of None
                text=response,
                sender='bot'
            )
            db.session.add(bot_message)
            db.session.commit()
            
            return jsonify({
                'response': response,
                'audio_url': None  # Add audio URL if needed
            })
        except Exception as db_error:
            db.session.rollback()
            print(f"Database error in process_text: {str(db_error)}")
            raise
            
    except Exception as e:
        import traceback
        print(f"Error in process_text API: {str(e)}")
        print(traceback.format_exc())
        
        # Return a user-friendly error message in the appropriate language
        error_message = "I'm sorry, I encountered an error. Please try again." if language == 'english' else "मुझे खेद है, मुझे एक त्रुटि मिली। कृपया पुनः प्रयास करें।"
        
        return jsonify({
            'error': str(e),
            'response': error_message
        }), 500

@app.route('/api/process_voice', methods=['POST'])
@login_required
def process_voice():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    language = request.form.get('language', 'hindi')
    chat_id = request.form.get('chat_id')
    
    # Get user_id if authenticated
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Get system user id for bot messages
    system_user_id = get_or_create_system_user()
    
    # Validate chat_id to avoid foreign key constraint errors
    if not chat_id or chat_id == 'null' or chat_id == 'undefined':
        # Create a new chat session if none is specified
        try:
            new_chat = ChatSession(language=language, user_id=user_id)
            db.session.add(new_chat)
            db.session.commit()
            chat_id = new_chat.id
            print(f"Created new chat session with ID: {chat_id}")
        except Exception as e:
            print(f"Error creating chat session: {e}")
            return jsonify({'error': 'Failed to create chat session'}), 500
    else:
        # Verify the chat session exists
        chat_session = db.session.get(ChatSession, chat_id)
        if not chat_session:
            return jsonify({'error': f'Chat session {chat_id} not found'}), 404
    
    try:
        # Create directory if it doesn't exist
        voice_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'voice')
        os.makedirs(voice_dir, exist_ok=True)
        
        # Save audio file with unique filename
        # Keep the original extension to maintain compatibility
        original_filename = audio_file.filename
        original_ext = os.path.splitext(original_filename)[1].lower() or '.webm'
        
        # Force .wav extension if the file is actually wav (browser sometimes sends as webm)
        content_type = audio_file.content_type
        print(f"Audio content type: {content_type}")
        
        # Handle different content types appropriately
        if content_type == 'audio/wav' or content_type == 'audio/wave':
            save_ext = '.wav'
        elif content_type == 'audio/mpeg' or content_type == 'audio/mp3':
            save_ext = '.mp3'
        elif content_type == 'audio/ogg':
            save_ext = '.ogg'
        else:
            # Default to original extension or webm
            save_ext = original_ext
        
        filename = f"{uuid.uuid4()}{save_ext}"
        audio_path = os.path.join(voice_dir, filename)
        
        # Convert Windows backslashes to forward slashes
        audio_path_normalized = audio_path.replace('\\', '/')
        
        print(f"Saving audio file to: {audio_path_normalized}")
        audio_file.save(audio_path)
        
        # Verify the file was saved correctly
        if not os.path.exists(audio_path):
            return jsonify({'error': 'Failed to save audio file'}), 500
            
        print(f"Audio file saved at: {audio_path}")
        print(f"File size: {os.path.getsize(audio_path)} bytes")
        print(f"Content type: {content_type}")
        
        # Process audio to text using our local model
        transcribed_text = speech_to_text(audio_path, language)
        print(f"Transcription result: {transcribed_text}")
        
        # Check for specific error indicators
        error_indicators = [
            "[Audio transcription failed]",
            "[ऑडियो ट्रांसक्रिप्शन विफल]",
            "[Audio preprocessing failed]",
            "[ऑडियो प्रीप्रोसेसिंग विफल हुई]",
            "[Audio file not found]",
            "[ऑडियो फ़ाइल नहीं मिली]",
            "[Audio processing error]",
            "[ऑडियो प्रोसेसिंग त्रुटि]"
        ]
        
        # If transcription error, return a UI-friendly message, but not a server error
        if any(indicator in transcribed_text for indicator in error_indicators):
            # Add the transcription error as a user message so the conversation can continue
            user_message = ChatMessage(
                chat_id=chat_id,
                user_id=user_id,
                text="[Voice input - could not be transcribed]",
                sender='user',
                input_type='voice'
            )
            db.session.add(user_message)
            
            # Add a helpful bot response
            help_text = "I couldn't understand your audio. Please try typing your message or speaking more clearly." if language == 'english' else "मुझे आपकी आवाज़ समझ नहीं आई। कृपया अपना संदेश टाइप करें या स्पष्ट रूप से बोलें।"
            bot_message = ChatMessage(
                chat_id=chat_id,
                user_id=system_user_id,  # Use system user instead of None
                text=help_text,
                sender='bot'
            )
            db.session.add(bot_message)
            db.session.commit()
            
            # Return the response to show in UI, but with a warning
            return jsonify({
                'transcribed_text': transcribed_text,
                'response': help_text,
                'chat_id': chat_id,
                'warning': 'Audio could not be transcribed properly'
            })
        
        # Save user message with transcribed text
        user_message = ChatMessage(
            chat_id=chat_id,
            user_id=user_id,
            text=transcribed_text,
            sender='user',
            input_type='voice'
        )
        db.session.add(user_message)
        
        # Get response from text processing
        response = process_text_query(transcribed_text, language)
        print(response)
        # Save bot response
        bot_message = ChatMessage(
            chat_id=chat_id,
            user_id=system_user_id,  # Use system user instead of None
            text=response,
            sender='bot'
        )
        db.session.add(bot_message)
        db.session.commit()
        
        # Generate TTS - now using local TTS model
        audio_response_path = text_to_speech(response, language)
        print(audio_response_path)
        # Check if the file exists and is a valid audio file
        audio_valid = False
        if os.path.exists(audio_response_path):
            if audio_response_path.lower().endswith(('.mp3', '.wav')):
                # Basic validation - check file size
                if os.path.getsize(audio_response_path) > 1000:  # More than 1KB
                    audio_valid = True
        
        # Get the audio URL for the client
        if audio_valid:
            # Make sure to normalize path for URLs
            audio_response_path = audio_response_path.replace('\\', '/')
            if audio_response_path.startswith('static/'):
                audio_url = url_for('static', filename=audio_response_path.replace('static/', ''))
            else:
                # Handle non-static paths
                audio_url = audio_response_path

            # print that we are returning the the response
            print("Returning the response", {
                'transcribed_text': transcribed_text,
                'response': response,
                'audio_url': audio_url,
                'chat_id': chat_id
            })
                
            return jsonify({
                'transcribed_text': transcribed_text,
                'response': response,
                'audio_url': audio_url,
                'chat_id': chat_id
            })
        else:
            # No valid audio, just return the text response


            return jsonify({
                'transcribed_text': transcribed_text,
                'response': response,
                'chat_id': chat_id,
                'warning': 'Text-to-speech output is not available'
            })
    
    except Exception as e:
        import traceback
        print(f"Error in process_voice: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()  # Rollback any pending database changes
        
        # Provide a user-friendly error message based on language
        error_msg = "Error processing voice: Please try again or type your message." if language == 'english' else "आवाज़ प्रोसेसिंग में त्रुटि: कृपया पुनः प्रयास करें या अपना संदेश टाइप करें।"
        
        return jsonify({
            'error': error_msg,
            'detail': str(e)
        }), 500

@app.route('/api/process_image', methods=['POST'])
@login_required
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    image_file = request.files['image']
    language = request.form.get('language', 'hindi')
    chat_id = request.form.get('chat_id')
    
    # Get user_id if authenticated
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Get system user id for bot messages
    system_user_id = get_or_create_system_user()
    
    # Validate chat_id to avoid foreign key constraint errors
    if not chat_id or chat_id == 'null' or chat_id == 'undefined':
        # Create a new chat session if none is specified
        try:
            new_chat = ChatSession(language=language, user_id=user_id)
            db.session.add(new_chat)
            db.session.commit()
            chat_id = new_chat.id
            print(f"Created new chat session with ID: {chat_id}")
        except Exception as e:
            print(f"Error creating chat session: {e}")
            return jsonify({'error': 'Failed to create chat session'}), 500
    else:
        # Verify the chat session exists
        chat_session = db.session.get(ChatSession, chat_id)
        if not chat_session:
            return jsonify({'error': f'Chat session {chat_id} not found'}), 404
    
    # Save image
    filename = f"{uuid.uuid4()}{os.path.splitext(image_file.filename)[1]}"
    
    # Ensure directory exists
    image_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
    os.makedirs(image_dir, exist_ok=True)
    
    image_path = os.path.join(image_dir, filename)
    image_file.save(image_path)
    image_path = image_path.replace("\\", "/")

    # Generate the URL for the image
    url_path = f"uploads/images/{filename}".replace("\\", "/")
    image_url = url_for('static', filename=url_path)

    # Analyze image
    try:
        result = analyze_plant_image(image_path, language)
        
        print(result)

        # Create user message - include image URL in the message for persistence
        user_message = ChatMessage(
            chat_id=chat_id,
            user_id=user_id,
            text=f"<img src='{image_url}' class='plant-diagnosis-image'><br>Plant image uploaded for diagnosis",
            sender='user',
            input_type='image'
        )
        db.session.add(user_message)
        db.session.flush()  # Get the ID without committing
        message_id = user_message.id
        
        # Create response text
        response_text = f"Plant type: {result['plant_type']}\nDisease: {result['disease']}\nConfidence: {result['confidence']:.2f}\nRecommendation: {result['recommendation']}"
        
        print(response_text)

        # Create bot message
        bot_message = ChatMessage(
            chat_id=chat_id,
            user_id=system_user_id,  # Use system user instead of None
            text=response_text,
            sender='bot'
        )
        db.session.add(bot_message)
        
        # Create a PlantImage record
        plant_image = PlantImage(
            chat_id=chat_id,
            user_id=user_id,
            # message_id=message_id,
            image_path=image_path,
            plant_type=result['plant_type'],
            disease=result['disease'],
            confidence=result['confidence'],
            recommendation=result['recommendation']
        )
        db.session.add(plant_image)
        db.session.commit()
        
        # Generate TTS if needed
        audio_url = None
        if request.form.get('need_audio', 'false').lower() == 'true':
            audio_path = text_to_speech(response_text, language)
            audio_url = url_for('static', filename=audio_path.replace('static/', ''))
        
        return jsonify({
            'result': result,
            'image_url': image_url,
            'audio_url': audio_url,
            'chat_id': chat_id  # Return the chat_id for client tracking
        })
    
    except Exception as e:
        import traceback
        print(f"Error in process_image: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        preferred_language = request.form.get('language')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # Convert empty strings to None
        latitude = float(latitude) if latitude and latitude.strip() else None
        longitude = float(longitude) if longitude and longitude.strip() else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET username = %s, preferred_language = %s, latitude = %s, longitude = %s WHERE id = %s",
            (username, preferred_language, latitude, longitude, current_user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update session
        current_user.username = username
        current_user.preferred_language = preferred_language
        current_user.latitude = latitude
        current_user.longitude = longitude
        
        flash('Profile updated successfully')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/api/change_password', methods=['POST'])
@login_required
def change_password():
    """
    API endpoint to update user password
    """
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form inputs
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
            
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
            
        # Verify current password
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (current_user.id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
        # Check if current password is correct
        if not check_password_hash(user_data['password_hash'], current_password):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
            
        # Hash the new password
        password_hash = generate_password_hash(new_password)
        
        # Update password in database
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, current_user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password updated successfully'})
        
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/delete_account', methods=['POST'])
@login_required
def delete_account():
    """
    API endpoint to delete a user account
    """
    try:
        # Get confirmation from form
        confirmation = request.form.get('confirmation', '').lower()
        
        if confirmation != 'delete':
            return jsonify({'success': False, 'message': 'Confirmation text does not match'}), 400
            
        user_id = current_user.id
        
        # Log the user out first
        logout_user()
        
        # Delete the user from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First, delete or anonymize related data
        # This depends on your database constraints and data retention policies
        # For example, you might want to:
        # 1. Delete chat sessions
        cursor.execute("DELETE FROM chat_sessions WHERE user_id = %s", (user_id,))
        
        # 2. Delete plant images
        cursor.execute("DELETE FROM plant_images WHERE user_id = %s", (user_id,))
        
        # 3. Delete soil reports
        cursor.execute("DELETE FROM soil_reports WHERE user_id = %s", (user_id,))
        
        # 4. Delete chat messages
        cursor.execute("DELETE FROM chat_messages WHERE user_id = %s", (user_id,))
        
        # Finally, delete the user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting account: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/history')
@login_required
def history():
    from ast import literal_eval  # Safe parsing
    
    # Get user_id if authenticated
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Filter chat sessions by user_id
    if user_id:
        chat_sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
        plant_images = PlantImage.query.filter_by(user_id=user_id).order_by(PlantImage.timestamp.desc()).all()
        soil_reports = SoilReport.query.filter_by(user_id=user_id).order_by(SoilReport.created_at.desc()).all()
    else:
        chat_sessions = ChatSession.query.filter_by(user_id=None).order_by(ChatSession.created_at.desc()).all()
        plant_images = PlantImage.query.filter_by(user_id=None).order_by(PlantImage.timestamp.desc()).all()
        soil_reports = SoilReport.query.filter_by(user_id=None).order_by(SoilReport.created_at.desc()).all()
    
    # For each chat session, get the first message for preview
    for session in chat_sessions:
        first_message = ChatMessage.query.filter_by(chat_id=session.id).order_by(ChatMessage.timestamp).first()
        if first_message:
            session.sample = first_message
            session.message_count = ChatMessage.query.filter_by(chat_id=session.id).count()
        else:
            session.sample = None
            session.message_count = 0

    # --- 💡 Convert crop_recommendations for each soil_report ---
    for report in soil_reports:
        if isinstance(report.crop_recommendations, str):
            try:
                report.crop_recommendations = literal_eval(report.crop_recommendations)
            except Exception as e:
                print("Error parsing crop_recommendations:", e)
                report.crop_recommendations = []  # fallback if parsing fails

    return render_template('history.html', 
                          chat_sessions=chat_sessions,
                          plant_images=plant_images,
                          soil_reports=soil_reports)


@app.route('/chat_session/<chat_id>')
@login_required
def chat_session(chat_id):
    # Get the chat session
    chat = db.session.get(ChatSession, chat_id)
    if not chat:
        flash('Chat session not found', 'error')
        return redirect(url_for('history'))
    
    # Security check: Make sure the user can only access their own chats
    if current_user.is_authenticated:
        if chat.user_id is not None and chat.user_id != current_user.id:
            flash('You do not have permission to view this chat', 'error')
            return redirect(url_for('history'))
    else:
        # Non-authenticated users can only access chats with no user_id
        if chat.user_id is not None:
            flash('You do not have permission to view this chat', 'error')
            return redirect(url_for('chat'))
    
    # Get all messages for the chat session
    messages = ChatMessage.query.filter_by(chat_id=chat_id).order_by(ChatMessage.timestamp).all()
    
    return render_template('chat_session.html', 
                          chat=chat,
                          messages=messages,
                          language=chat.language)

@app.route('/soil_report')
@login_required
def soil_report():
    """
    Render the soil report analysis page
    """
    # Get language from query parameter or user preference
    language = request.args.get('language')
    
    if not language and current_user.is_authenticated:
        language = current_user.preferred_language
    
    if not language:
        language = 'english'  # Default language
        
    return render_template('soil_report.html', language=language)

@app.route('/api/analyze_soil_report', methods=['POST'])
@login_required
def analyze_soil_report():
    """
    Process a soil report file (PDF, image, etc.) and extract parameters using OpenRouter's Gemini model
    """
    if 'soil_report' not in request.files:
        return jsonify({'error': 'No soil report provided'}), 400
    
    # Import at the beginning of the function to avoid scope issues
    from models.chat_model import ChatSession, db, SoilReport
    
    soil_file = request.files['soil_report']
    district = request.form.get('district')
    state = request.form.get('state')
    language = request.form.get('language', 'english')
    
    # Validate file format
    allowed_mimetypes = [
        'image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp',
        'application/pdf', 'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    # Get the mimetype from the filename
    import mimetypes
    file_mimetype = mimetypes.guess_type(soil_file.filename)[0]
    
    if file_mimetype not in allowed_mimetypes:
        file_ext = os.path.splitext(soil_file.filename)[1].lower()
        if file_ext not in ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.bmp', '.tiff', '.webp']:
            return jsonify({'error': 'Unsupported file format. Please upload a PDF or image file.'}), 400
    
    # Get user_id if authenticated
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Get the chat_id from the form or create a new chat session
    chat_id = request.form.get('chat_id')
    
    # If no chat_id provided or it's invalid, create a new chat session
    if not chat_id or chat_id == 'standalone' or chat_id == 'null' or chat_id == 'undefined':
        try:
            # Create a new chat session
            new_chat = ChatSession(language=language, user_id=user_id)
            db.session.add(new_chat)
            db.session.flush()  # Flush to get the ID without committing
            chat_id = new_chat.id
            print(f"Created new chat session with ID: {chat_id}")
        except Exception as e:
            print(f"Error creating chat session: {e}")
            return jsonify({'error': 'Failed to create chat session'}), 500
    else:
        # Verify the chat session exists
        chat_session = db.session.get(ChatSession, chat_id)
        if not chat_session:
            return jsonify({'error': f'Chat session {chat_id} not found'}), 404
    
    # Save file
    filename = f"{uuid.uuid4()}{os.path.splitext(soil_file.filename)[1]}"
    
    # Ensure directory exists
    soil_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'soil_reports')
    os.makedirs(soil_dir, exist_ok=True)
    
    file_path = os.path.join(soil_dir, filename)
    soil_file.save(file_path)
    file_path = file_path.replace("\\", "/")
    
    # Convert file to image for processing
    success, result = convert_file_to_image(file_path)
    
    if not success:
        # If conversion failed, return the error message
        return jsonify({'error': result}), 400
    
    # Now result contains the image as a numpy array
    # Process soil report using OpenRouter's Gemini Pro Vision model
    try:
        import requests
        import base64
        from PIL import Image as PILImage
        import io
        import numpy as np
        
        # Get OpenRouter API key
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_api_key:
            return jsonify({'error': 'OpenRouter API key not configured'}), 500
        
        # Convert numpy array to PIL Image
        image = PILImage.fromarray(result)
        
        # Resize image if it's too large (max dimension 768px for better compatibility)
        max_size = 768
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, PILImage.LANCZOS)
        
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=90)
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Prepare the OpenRouter API request
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare the prompt
        prompt = """
        You're a soil analysis expert. Extract all available soil parameters from this soil report image.
        I need exact numeric values for:
        - pH
        - EC (Electrical Conductivity)
        - Organic Carbon
        - Nitrogen
        - Phosphorus
        - Potassium
        - Zinc
        - Copper
        - Iron
        - Manganese
        - Sulphur
        
        ALSO, look for and extract location information ONLY if the words "District" and "State" are EXPLICITLY mentioned in the report:
        - District (only if labeled as "District" or "DISTRICT" in the report)
        - State (only if labeled as "State" or "STATE" in the report)

        Return only a JSON object with these parameters as keys and their values. 
        For soil parameters, use numeric values without units. 
        For district and state, use string values with quotes.

        IMPORTANT: If a parameter is not visible or clearly mentioned in the report, set its value to null (not 0 or any default value).
        
        Example response format:
        {
            "ph": 7.2,
            "ec": 0.45,
            "organic_carbon": 0.65,
            "nitrogen": 250,
            "phosphorus": 28.5,
            "potassium": 156,
            "zinc": 0.8,
            "copper": 0.6,
            "iron": 4.5,
            "manganese": 2.2,
            "sulphur": 20,
        }
        
        If no district or state is explicitly mentioned, return null for those fields like:
        "district": null,
        "state": null
        """
        
        # Create the request payload
        payload = {
            "model": "qwen/qwen2.5-vl-3b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                    ]
                }
            ]
        }
        
        # Send the request to OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.text}")
        
        # Extract the text response
        response_data = response.json()
        print(response_data)
        response_text = response_data["choices"][0]["message"]["content"]
        print(response_text)
        # Extract the JSON part from the response
        import re
        
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            soil_params_json = json_match.group(1)
        else:
            json_match = re.search(r'{.*}', response_text, re.DOTALL)
            if json_match:
                soil_params_json = json_match.group(0)
            else:
                soil_params_json = '{}'
        
        # Parse the JSON
        try:
            soil_params = json.loads(soil_params_json)
            
            # Ensure district and state are proper values, not literal strings "null"
            if soil_params.get('district') == "null" or soil_params.get('district') == "None":
                soil_params['district'] = None
                
            if soil_params.get('state') == "null" or soil_params.get('state') == "None":
                soil_params['state'] = None
                
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Attempted to parse: {soil_params_json}")
            soil_params = {}
        
        # Extract district and state from soil_params if available, otherwise use form inputs
        extracted_district = soil_params.get('district')
        extracted_state = soil_params.get('state')
        
        # Track if location information was extracted from the report
        # Only consider a value extracted if it's not None and not the string "null"
        district_extracted = (extracted_district is not None and 
                            extracted_district != "null" and 
                            str(extracted_district).lower() != "none" and
                            str(extracted_district).strip() != "")
        
        state_extracted = (extracted_state is not None and 
                          extracted_state != "null" and 
                          str(extracted_state).lower() != "none" and
                          str(extracted_state).strip() != "")
        
        # If location was provided in the form, use that; otherwise use extracted values
        final_district = district if district and district.strip() != '' else (extracted_district if district_extracted else '')
        final_state = state if state and state.strip() != '' else (extracted_state if state_extracted else '')
        
        # Check if we have both district and state information
        missing_location = (not final_district or not final_state or 
                           final_district.strip() == '' or final_state.strip() == '')
        
        # Remove district and state from soil_params to avoid confusion
        if 'district' in soil_params:
            del soil_params['district']
        if 'state' in soil_params:
            del soil_params['state']
            
        # If location information is missing, return what we have extracted so far 
        # so the frontend can show a popup to collect the missing information
        if missing_location:
            return jsonify({
                'soil_params': soil_params,
                'location': {
                    'district': final_district or '',
                    'state': final_state or '',
                    'district_extracted': district_extracted,
                    'state_extracted': state_extracted
                },
                'missing_location': True,
                'report_path': file_path,
                'language': language
            })
        
        # Make sure all required parameters have at least default values
        if soil_params.get('ph') is None:
            soil_params['ph'] = 7.0
        if soil_params.get('ec') is None:
            soil_params['ec'] = 0.5
        if soil_params.get('organic_carbon') is None:
            soil_params['organic_carbon'] = 0.5
        if soil_params.get('nitrogen') is None:
            soil_params['nitrogen'] = 250.0
        if soil_params.get('phosphorus') is None:
            soil_params['phosphorus'] = 30.0
        if soil_params.get('potassium') is None:
            soil_params['potassium'] = 40.0
        if soil_params.get('zinc') is None:
            soil_params['zinc'] = 1.0
        if soil_params.get('copper') is None:
            soil_params['copper'] = 0.5
        if soil_params.get('iron') is None:
            soil_params['iron'] = 4.0
        if soil_params.get('manganese') is None:
            soil_params['manganese'] = 2.0
        if soil_params.get('sulphur') is None:
            soil_params['sulphur'] = 20.0
            
        # Get crop prediction
        predicted_crop = predict_crop(
            distt=final_district,
            state=final_state,
            ph=soil_params.get('ph', 7.0),
            ec=soil_params.get('ec', 0.5),
            oc=soil_params.get('organic_carbon', 0.5),
            av_p=soil_params.get('phosphorus', 30.0),
            av_k=soil_params.get('potassium', 40.0),
            zinc=soil_params.get('zinc', 1.0),
            cu=soil_params.get('copper', 0.5),
            iron=soil_params.get('iron', 4.0),
            mn=soil_params.get('manganese', 2.0)
        )
        print(predicted_crop)
        # Get crop variety information
        crop_variety_data = get_crop_varieties(predicted_crop)
        print(crop_variety_data)
        # Add additional crop suggestions based on soil parameters
        recommended_crops = [predicted_crop]
        predicted_crop = predicted_crop.lower()
        if predicted_crop != "wheat":
            recommended_crops.append("Wheat")
        if predicted_crop != "rice":
            recommended_crops.append("Rice") 
        if predicted_crop != "maize":
            recommended_crops.append("Maize")
        
        print(recommended_crops)

        # Generate fertilizer recommendations
        fertilizer_recommendations = generate_fertilizer_recommendations(soil_params)
        fertilizer_rec = fertilizer_recommendations.get('summary', 
            "Based on the soil analysis, apply balanced NPK fertilizer.")
        
        # Store the full fertilizer report for later use
        full_fertilizer_report = fertilizer_recommendations.get('full_report', "")
        json_fertilizer_report = fertilizer_recommendations.get('json_report', None)
        # Convert json_fertilizer_report to string if it's a dictionary
        if isinstance(json_fertilizer_report, dict):
            json_fertilizer_report = json.dumps(json_fertilizer_report)
        
        # Get soil type based on pH
        soil_type = "Neutral Soil"
        if soil_params.get('ph', 7.0) < 6.0:
            soil_type = "Acidic Soil"
        elif soil_params.get('ph', 7.0) > 7.5:
            soil_type = "Alkaline Soil"
        
        # Create a new SoilReport record in the database
        soil_report = SoilReport(
            user_id=user_id,
            chat_id=chat_id,  # Use the valid chat_id we ensured above
            report_path=file_path,
            district=final_district,
            state=final_state,
            soil_type=soil_type,
            ph_value=soil_params.get('ph'),  # Changed from ph to ph_value
            ec=soil_params.get('ec'),
            organic_carbon=soil_params.get('organic_carbon'),
            phosphorus=soil_params.get('phosphorus'),
            potassium=soil_params.get('potassium'),
            zinc=soil_params.get('zinc'),
            copper=soil_params.get('copper'),
            iron=soil_params.get('iron'),
            manganese=soil_params.get('manganese'),
            nitrogen=soil_params.get('nitrogen'),  # Added nitrogen field
            sulphur=soil_params.get('sulphur'),      # Added sulphur field
            predicted_crop=predicted_crop,
            crop_recommendations=json.dumps(recommended_crops),
            fertilizer_recommendations=json.dumps({"summary": fertilizer_rec}),
            full_fertilizer_report=full_fertilizer_report,
            json_fertilizer_report=json_fertilizer_report
        )
        
        db.session.add(soil_report)
        db.session.commit()
        
        # Prepare the response
        result = {
            'soil_params': soil_params,
            'location': {
                'district': final_district,
                'state': final_state,
                'district_extracted': district_extracted,
                'state_extracted': state_extracted
            },
            'recommendations': {
                'crops': recommended_crops,
                'fertilizer': fertilizer_rec
            },
            'crop_varieties': crop_variety_data,
            'soil_report_id': soil_report.id  # Add the ID for the fertilizer report link
        }
        print(result)
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        print(f"Error in analyze_soil_report: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear_chat', methods=['POST'])
@login_required
def clear_chat():
    try:
        # Generate a new chat ID instead of deleting history
        chat_id = str(uuid.uuid4())
        session['current_chat_id'] = chat_id
        
        return jsonify({'success': True, 'message': 'New chat session created successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/utility/fix_paths')
@login_required
def fix_paths():
    if not current_user.is_authenticated:
        flash('You need to be logged in to access this utility')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fix plant diagnosis paths
        cursor.execute("SELECT id, image_path FROM plant_images")
        plant_images = cursor.fetchall()
        
        for diagnosis in plant_images:
            if '\\' in diagnosis['image_path']:
                fixed_path = diagnosis['image_path'].replace('\\', '/')
                cursor.execute(
                    "UPDATE plant_images SET image_path = %s WHERE id = %s",
                    (fixed_path, diagnosis['id'])
                )
        
        # Fix soil report paths
        cursor.execute("SELECT id, report_path FROM soil_reports")
        soil_reports = cursor.fetchall()
        
        for report in soil_reports:
            if '\\' in report['report_path']:
                fixed_path = report['report_path'].replace('\\', '/')
                cursor.execute(
                    "UPDATE soil_reports SET report_path = %s WHERE id = %s",
                    (fixed_path, report['id'])
                )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('All file paths have been fixed')
        return redirect(url_for('history'))
    
    except Exception as e:
        flash(f'Error fixing paths: {str(e)}')
        return redirect(url_for('history'))

@app.route('/api/delete_chat/<chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    try:
        # Find the chat session
        chat_session = db.session.get(ChatSession, chat_id)
        
        if not chat_session:
            return jsonify({'success': False, 'error': 'Chat session not found'}), 404
        
        # Check if the user owns this chat (if authenticated)
        if current_user.is_authenticated:
            if chat_session.user_id != current_user.id:
                return jsonify({'success': False, 'error': 'You do not have permission to delete this chat'}), 403
        else:
            # For non-authenticated users, only allow deletion of chats with no user_id
            if chat_session.user_id is not None:
                return jsonify({'success': False, 'error': 'You do not have permission to delete this chat'}), 403
        
        # Delete the chat session (this will cascade delete all messages)
        db.session.delete(chat_session)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/fertilizer_report/<report_id>')
@login_required
def fertilizer_report(report_id):
    """
    Display the detailed fertilizer recommendation report
    """
    try:
        # Get the soil report from the database
        soil_report = db.session.get(SoilReport, report_id)
        
        if not soil_report:
            return render_template('error.html', message="Soil report not found")
        
        # Extract report data
        data = {
            'report_id': soil_report.id,
            'farmer_name': "Farmer", # Default value
            'district': soil_report.district,
            'state': soil_report.state,
            'crop': soil_report.predicted_crop,
            'report_date': soil_report.created_at.strftime('%d-%b-%Y'),
            'full_report': soil_report.full_fertilizer_report,
            'json_report': None
        }

        # Parse json_fertilizer_report if it exists
        if soil_report.json_fertilizer_report:
            try:
                data['json_report'] = json.loads(soil_report.json_fertilizer_report)
            except (json.JSONDecodeError, TypeError):
                # If it's already a dict or can't be parsed, use as is
                data['json_report'] = soil_report.json_fertilizer_report

        # Get crop data from database.json if available
        if soil_report.predicted_crop:
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                database_path = os.path.join(current_dir, 'data', 'database.json')
                if os.path.exists(database_path):
                    with open(database_path, 'r', encoding='utf-8') as file:
                        crop_database = json.load(file)
                    
                    # Normalize the key for case-insensitive match
                    crop_key = next((key for key in crop_database if key.lower() == soil_report.predicted_crop.lower()), None)
                    if crop_key:
                        data['crop_data'] = crop_database[crop_key]
            except Exception as e:
                print(f"Error loading crop data: {e}")
        
        # If user is logged in, try to get their name
        if current_user.is_authenticated and soil_report.user_id == current_user.id:
            data['farmer_name'] = current_user.username
            
        return render_template('fertilizer_report.html', data=data)
    
    except Exception as e:
        import traceback
        print(f"Error in fertilizer_report: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', message=f"Error loading report: {str(e)}")

@app.route('/api/fertilizer_report/<report_id>/pdf')
@login_required
def download_fertilizer_report(report_id):
    """
    Generate and download a PDF of the fertilizer recommendation report
    """
    try:
        from flask import send_file
        import tempfile
        import pdfkit
        from jinja2 import Template
        
        # Get the soil report
        soil_report = db.session.get(SoilReport, report_id)
        
        if not soil_report:
            return jsonify({'error': 'Report not found'}), 404
            
        # Create a simple HTML template for the PDF
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Fertilizer Recommendation Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 20px; }
                .section { margin-bottom: 15px; }
                table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                table, th, td { border: 1px solid #ddd; }
                th, td { padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Fertilizer Recommendation Report</h1>
                <p>Farmer: {{farmer_name}} | Location: {{district}}, {{state}} | Date: {{report_date}}</p>
                <p>Crop: {{crop}}</p>
            </div>
            <div class="content">
                <pre>{{full_report}}</pre>
            </div>
        </body>
        </html>
        """
        
        # Render the template with data
        farmer_name = "Farmer"  # Default
        if current_user.is_authenticated and soil_report.user_id == current_user.id:
            farmer_name = current_user.username
            
        template = Template(html_content)
        rendered_html = template.render(
            farmer_name=farmer_name,
            district=soil_report.district or "N/A",
            state=soil_report.state or "N/A",
            report_date=soil_report.created_at.strftime('%d-%b-%Y'),
            crop=soil_report.predicted_crop or "N/A",
            full_report=soil_report.full_fertilizer_report or "No report available"
        )
        
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
            
        # Generate PDF using pdfkit
        pdfkit_config = pdfkit.configuration(wkhtmltopdf='wkhtmltopdf')
        pdfkit.from_string(rendered_html, pdf_path, configuration=pdfkit_config)
        
        # Send the file to the user
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"fertilizer_report_{report_id}.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        import traceback
        print(f"Error generating PDF: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/complete_soil_analysis', methods=['POST'])
@login_required
def complete_soil_analysis():
    """
    Complete soil report analysis with user-provided location information
    This endpoint is used when the initial analysis couldn't extract location data
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract data from the request
        soil_params = data.get('soil_params', {})
        district = data.get('district', '').strip()
        state = data.get('state', '').strip()
        language = data.get('language', 'english')
        report_path = data.get('report_path', '')
        
        # Validate inputs - ensure we have both location fields
        if not district:
            return jsonify({'error': 'District is required'}), 400
        
        if not state:
            return jsonify({'error': 'State is required'}), 400
        
        if not report_path or not os.path.exists(report_path):
            return jsonify({'error': 'Valid report path is required'}), 400
        
        # Get user_id if authenticated
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Get or create chat session
        chat_id = data.get('chat_id')
        if not chat_id or chat_id == 'null' or chat_id == 'undefined':
            try:
                # Create a new chat session
                new_chat = ChatSession(language=language, user_id=user_id)
                db.session.add(new_chat)
                db.session.flush()  # Flush to get the ID without committing
                chat_id = new_chat.id
            except Exception as e:
                print(f"Error creating chat session: {e}")
                return jsonify({'error': 'Failed to create chat session'}), 500
        else:
            # Verify the chat session exists
            chat_session = db.session.get(ChatSession, chat_id)
            if not chat_session:
                return jsonify({'error': f'Chat session {chat_id} not found'}), 404
        
        
        # Make sure all required parameters have at least default values
        if soil_params.get('ph') is None:
            soil_params['ph'] = 7.0
        if soil_params.get('ec') is None:
            soil_params['ec'] = 0.5
        if soil_params.get('organic_carbon') is None:
            soil_params['organic_carbon'] = 0.5
        if soil_params.get('nitrogen') is None:
            soil_params['nitrogen'] = 250.0
        if soil_params.get('phosphorus') is None:
            soil_params['phosphorus'] = 30.0
        if soil_params.get('potassium') is None:
            soil_params['potassium'] = 40.0
        if soil_params.get('zinc') is None:
            soil_params['zinc'] = 1.0
        if soil_params.get('copper') is None:
            soil_params['copper'] = 0.5
        if soil_params.get('iron') is None:
            soil_params['iron'] = 4.0
        if soil_params.get('manganese') is None:
            soil_params['manganese'] = 2.0
        if soil_params.get('sulphur') is None:
            soil_params['sulphur'] = 20.0
            
        # Get crop prediction
        predicted_crop = predict_crop(
            distt=district,
            state=state,
            ph=soil_params.get('ph', 7.0),
            ec=soil_params.get('ec', 0.5),
            oc=soil_params.get('organic_carbon', 0.5),
            av_p=soil_params.get('phosphorus', 30.0),
            av_k=soil_params.get('potassium', 40.0),
            zinc=soil_params.get('zinc', 1.0),
            cu=soil_params.get('copper', 0.5),
            iron=soil_params.get('iron', 4.0),
            mn=soil_params.get('manganese', 2.0)
        )
        
        # Get crop variety information
        crop_variety_data = get_crop_varieties(predicted_crop)
        
        # Add additional crop suggestions based on soil parameters
        recommended_crops = [predicted_crop]
        predicted_crop_lower = predicted_crop.lower()
        if predicted_crop_lower != "wheat":
            recommended_crops.append("Wheat")
        if predicted_crop_lower != "rice":
            recommended_crops.append("Rice") 
        if predicted_crop_lower != "maize":
            recommended_crops.append("Maize")
        
        # Generate fertilizer recommendations
        fertilizer_recommendations = generate_fertilizer_recommendations(soil_params)
        fertilizer_rec = fertilizer_recommendations.get('summary', 
            "Based on the soil analysis, apply balanced NPK fertilizer.")
        
        # Store the full fertilizer report for later use
        full_fertilizer_report = fertilizer_recommendations.get('full_report', "")
        json_fertilizer_report = fertilizer_recommendations.get('json_report', None)
        
        # Convert json_fertilizer_report to string if it's a dictionary
        if isinstance(json_fertilizer_report, dict):
            json_fertilizer_report = json.dumps(json_fertilizer_report)
        
        # Get soil type based on pH
        soil_type = "Neutral Soil"
        if soil_params.get('ph', 7.0) < 6.0:
            soil_type = "Acidic Soil"
        elif soil_params.get('ph', 7.0) > 7.5:
            soil_type = "Alkaline Soil"
        
        # Create a new SoilReport record in the database
        soil_report = SoilReport(
            user_id=user_id,
            chat_id=chat_id,
            report_path=report_path,
            district=district,
            state=state,
            soil_type=soil_type,
            ph_value=soil_params.get('ph'),
            ec=soil_params.get('ec'),
            organic_carbon=soil_params.get('organic_carbon'),
            phosphorus=soil_params.get('phosphorus'),
            potassium=soil_params.get('potassium'),
            zinc=soil_params.get('zinc'),
            copper=soil_params.get('copper'),
            iron=soil_params.get('iron'),
            manganese=soil_params.get('manganese'),
            nitrogen=soil_params.get('nitrogen'),
            sulphur=soil_params.get('sulphur'),
            predicted_crop=predicted_crop_lower,
            crop_recommendations=json.dumps(recommended_crops),
            fertilizer_recommendations=json.dumps({"summary": fertilizer_rec}),
            full_fertilizer_report=full_fertilizer_report,
            json_fertilizer_report=json_fertilizer_report
        )
        
        db.session.add(soil_report)
        db.session.commit()
        
        # Prepare the response
        result = {
            'soil_params': soil_params,
            'location': {
                'district': district,
                'state': state
            },
            'recommendations': {
                'crops': recommended_crops,
                'fertilizer': fertilizer_rec
            },
            'crop_varieties': crop_variety_data,
            'soil_report_id': soil_report.id
        }
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"Error in complete_soil_analysis: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/pricing')
def pricing():
    """
    Render the pricing plans page
    This page is accessible to both authenticated and non-authenticated users
    """
    return render_template('pricing.html')

@app.route('/weather')
@login_required
def weather():
    """
    Render the weather analysis page
    """
    latitude = None
    longitude = None
    
    if current_user.is_authenticated:
        latitude = current_user.latitude
        longitude = current_user.longitude
        
    return render_template('weather.html', latitude=latitude, longitude=longitude)

@app.route('/api/weather')
@login_required
def get_weather():
    """
    API endpoint to fetch weather data from Meteo API
    """
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
            
        # Convert to float
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return jsonify({'error': 'Invalid coordinates format'}), 400
        
        # Call Meteo API
        import requests
        from datetime import datetime, timedelta
        
        # Basic location name lookup based on coordinates (simplified)
        location_name = get_location_name(lat, lon)
        
        # Meteo API URL
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relativehumidity_2m,precipitation,windspeed_10m&daily=weathercode,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_sum&current_weather=true&timezone=auto"
        
        response = requests.get(url)
        
        if response.status_code != 200:
            return jsonify({'error': f'Weather API error: {response.status_code}'}), 500
            
        data = response.json()
        
        # Process and structure the data
        current_weather = data.get('current_weather', {})
        hourly = data.get('hourly', {})
        daily = data.get('daily', {})
        
        # Current weather data
        current = {
            'temperature': current_weather.get('temperature', 0),
            'wind_speed': current_weather.get('windspeed', 0),
            'condition': get_weather_condition(current_weather.get('weathercode', 0)),
            'icon_url': get_weather_icon(current_weather.get('weathercode', 0)),
            'humidity': get_current_humidity(hourly),
            'feels_like': current_weather.get('temperature', 0),  # Simplified
            'precipitation': get_current_precipitation(hourly),
            'pressure': 1013,  # Default value as API doesn't provide pressure
            'uv_index': daily.get('uv_index_max', [0])[0] if daily.get('uv_index_max') else 0,
            'sunrise': format_time(daily.get('sunrise', [''])[0]) if daily.get('sunrise') else "06:00",
            'sunset': format_time(daily.get('sunset', [''])[0]) if daily.get('sunset') else "18:00"
        }
        
        # Hourly forecast - next 24 hours in 3-hour intervals
        hourly_forecast = []
        now = datetime.now()
        
        if hourly and hourly.get('time') and hourly.get('temperature_2m') and hourly.get('precipitation'):
            times = hourly.get('time', [])
            temps = hourly.get('temperature_2m', [])
            precips = hourly.get('precipitation', [])
            weather_codes = get_hourly_weather_codes(hourly, data)
            
            for i in range(0, min(len(times), 24), 3):
                hour_time = times[i]
                hour_dt = datetime.fromisoformat(hour_time.replace('Z', '+00:00'))
                
                if hour_dt < now:
                    continue
                    
                hourly_forecast.append({
                    'time': hour_dt.strftime('%H:%M'),
                    'temperature': temps[i] if i < len(temps) else 0,
                    'precipitation': precips[i] if i < len(precips) else 0,
                    'condition': get_weather_condition(weather_codes[i] if i < len(weather_codes) else 0),
                    'icon_url': get_weather_icon(weather_codes[i] if i < len(weather_codes) else 0)
                })
                
                if len(hourly_forecast) >= 8:  # Limit to 8 entries
                    break
        
        # Daily forecast - 7 days
        daily_forecast = []
        
        if daily and daily.get('time') and daily.get('temperature_2m_max') and daily.get('temperature_2m_min'):
            days = daily.get('time', [])
            max_temps = daily.get('temperature_2m_max', [])
            min_temps = daily.get('temperature_2m_min', [])
            weather_codes = daily.get('weathercode', [])
            precips = daily.get('precipitation_sum', [])
            
            for i in range(min(len(days), 7)):
                day_date = datetime.fromisoformat(days[i].replace('Z', '+00:00')) if i < len(days) else now + timedelta(days=i)
                
                daily_forecast.append({
                    'date': day_date.strftime('%d/%m'),
                    'day_of_week': day_date.strftime('%a'),
                    'temp_max': max_temps[i] if i < len(max_temps) else 0,
                    'temp_min': min_temps[i] if i < len(min_temps) else 0,
                    'precipitation': precips[i] if i < len(precips) else 0,
                    'condition': get_weather_condition(weather_codes[i] if i < len(weather_codes) else 0),
                    'icon_url': get_weather_icon(weather_codes[i] if i < len(weather_codes) else 0),
                    'humidity': 70  # Default value
                })
        
        # Simulate soil data - in a real app, this would come from sensors or another API
        soil_data = {
            'moisture_percent': 45,
            'temperature': 22
        }
        
        # Precipitation summaries
        precipitation_data = {
            'today': daily.get('precipitation_sum', [0])[0] if daily.get('precipitation_sum') else 0,
            'tomorrow': daily.get('precipitation_sum', [0, 0])[1] if daily.get('precipitation_sum') and len(daily.get('precipitation_sum')) > 1 else 0,
            'week': sum(daily.get('precipitation_sum', [0] * 7)[:7]) if daily.get('precipitation_sum') else 0
        }
        
        # Generate farming advice based on weather conditions
        farming_advice = generate_farming_advice(current, precipitation_data, soil_data)
        
        result = {
            'location_name': location_name,
            'current': current,
            'hourly': hourly_forecast,
            'daily': daily_forecast,
            'soil': soil_data,
            'precipitation': precipitation_data,
            'farming_advice': farming_advice
        }
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        print(f"Error in weather API: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500



# Add this helper function for system user at the top of the file, after the get_db_connection function
def get_or_create_system_user():
    """Get or create a system user for bot messages"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if system user exists
    cursor.execute("SELECT id FROM users WHERE email = 'system@farmerchatbot.com'")
    system_user = cursor.fetchone()
    
    if system_user:
        system_user_id = system_user['id']
    else:
        # Create system user if it doesn't exist
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, preferred_language) VALUES (%s, %s, %s, %s)",
            ('System', 'system@farmerchatbot.com', 'SYSTEM_USER_NOT_FOR_LOGIN', 'english')
        )
        conn.commit()
        system_user_id = cursor.lastrowid
    
    cursor.close()
    conn.close()
    return system_user_id

# Mandi Dashboard Routes
@app.route('/mandi')
@login_required
def mandi_dashboard():
    """
    Render the Mandi dashboard page
    """
    return render_template('mandi_dashboard.html')

@app.route('/api/mandi/states')
@login_required
def get_mandi_states():
    """
    Get list of unique states from mandi_data table
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT state FROM mandi_data ORDER BY state")
        states = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify(states)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandi/districts/<state>')
@login_required
def get_mandi_districts(state):
    """
    Get list of districts for a given state from mandi_data table
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT district FROM mandi_data WHERE state = %s ORDER BY district", (state,))
        districts = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify(districts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_mandi_dashboard_data(state=None, district=None, commodity=None, analysis_type='latest', start_date=None, end_date=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Base query
        query = """
            SELECT 
                market,
                commodity,
                variety,
                grade,
                arrival_date,
                min_price,
                max_price,
                modal_price
            FROM mandi_data
            WHERE 1=1
        """
        params = []

        # Add filters
        if state:
            query += " AND state = %s"
            params.append(state)
        if district and district.strip():
            query += " AND district = %s"
            params.append(district)
        if commodity and commodity.strip():
            query += " AND commodity = %s"
            params.append(commodity)

        # Handle analysis type
        if analysis_type == 'latest':
            # Get the latest date for the selected filters
            latest_date_query = f"""
                SELECT MAX(arrival_date) 
                FROM mandi_data 
                WHERE 1=1
            """
            if state:
                latest_date_query += " AND state = %s"
            if district and district.strip():
                latest_date_query += " AND district = %s"
            if commodity and commodity.strip():
                latest_date_query += " AND commodity = %s"
            
            cursor.execute(latest_date_query, params)
            latest_date = cursor.fetchone()[0]
            
            if latest_date:
                query += " AND arrival_date = %s"
                params.append(latest_date)
        else:  # past analysis
            if start_date and end_date:
                query += " AND arrival_date BETWEEN %s AND %s"
                params.extend([start_date, end_date])

        # Execute query
        cursor.execute(query, params)
        data = cursor.fetchall()

        # Process data for different visualizations
        result = {
            'table_data': [],
            'price_trends': {'labels': [], 'modal_prices': []},
            'commodity_distribution': {'labels': [], 'values': []},
            'market_comparison': {'labels': [], 'prices': []},
            'price_ranges': {'labels': [], 'ranges': []}
        }

        # Process data for table and charts
        for row in data:
            # Table data
            result['table_data'].append({
                'market': row[0],
                'commodity': row[1],
                'variety': row[2],
                'grade': row[3],
                'arrival_date': row[4],
                'min_price': row[5],
                'max_price': row[6],
                'modal_price': row[7]
            })

            # Price trends (only for past analysis)
            if analysis_type == 'past':
                result['price_trends']['labels'].append(row[4].strftime('%Y-%m-%d'))
                result['price_trends']['modal_prices'].append(float(row[7]))

            # Commodity distribution
            if row[1] not in result['commodity_distribution']['labels']:
                result['commodity_distribution']['labels'].append(row[1])
                result['commodity_distribution']['values'].append(1)
            else:
                idx = result['commodity_distribution']['labels'].index(row[1])
                result['commodity_distribution']['values'][idx] += 1

            # Market comparison
            if row[0] not in result['market_comparison']['labels']:
                result['market_comparison']['labels'].append(row[0])
                result['market_comparison']['prices'].append(float(row[7]))
            else:
                idx = result['market_comparison']['labels'].index(row[0])
                result['market_comparison']['prices'][idx] = (result['market_comparison']['prices'][idx] + float(row[7])) / 2

            # Price ranges
            if row[1] not in result['price_ranges']['labels']:
                result['price_ranges']['labels'].append(row[1])
                result['price_ranges']['ranges'].append([float(row[5]), float(row[7]), float(row[6])])
            else:
                idx = result['price_ranges']['labels'].index(row[1])
                current_range = result['price_ranges']['ranges'][idx]
                current_range[0] = min(current_range[0], float(row[5]))
                current_range[1] = (current_range[1] + float(row[7])) / 2
                current_range[2] = max(current_range[2], float(row[6]))

        return result

    except Exception as e:
        print(f"Error in get_mandi_dashboard_data: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

@app.route('/api/mandi/dashboard-data')
def mandi_dashboard_data():
    state = request.args.get('state')
    district = request.args.get('district')
    commodity = request.args.get('commodity')
    analysis_type = request.args.get('analysis_type', 'latest')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    data = get_mandi_dashboard_data(
        state=state,
        district=district,
        commodity=commodity,
        analysis_type=analysis_type,
        start_date=start_date,
        end_date=end_date
    )

    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500

@app.route('/api/user/location')
@login_required
def get_user_location():
    """
    Get user's location and determine their state
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'User not authenticated'}), 401
            
        # Get user's coordinates
        latitude = current_user.latitude
        longitude = current_user.longitude
        
        if not latitude or not longitude:
            return jsonify({'error': 'Location not set'}), 404
            
        # Use reverse geocoding to get state
        import requests
        
        # Using Nominatim for reverse geocoding
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
        headers = {'User-Agent': 'GreenSathi/1.0'}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return jsonify({'error': 'Geocoding service error'}), 500
            
        data = response.json()
        state = data.get('address', {}).get('state')
        
        if not state:
            return jsonify({'error': 'State not found'}), 404
            
        return jsonify({'state': state})
        
    except Exception as e:
        print(f"Error in get_user_location: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandi/commodities/<state>')
@login_required
def get_mandi_commodities(state):
    """
    Get list of unique commodities for a given state and district from mandi_data table
    """
    try:
        district = request.args.get('district', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base query
        query = "SELECT DISTINCT commodity FROM mandi_data WHERE state = %s"
        params = [state]
        
        # Add district filter if provided
        if district and district.strip():
            query += " AND district = %s"
            params.append(district)
            
        query += " ORDER BY commodity"
        
        cursor.execute(query, params)
        commodities = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify(commodities)
    except Exception as e:
        print(f"Error in get_mandi_commodities: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Advanced Mandi Analysis Routes
@app.route('/advance-mandi-analysis')
@login_required
def advance_mandi_analysis():
    """
    Render the advanced mandi analysis page
    """
    try:
        # Check if user has location set
        if not current_user.latitude or not current_user.longitude:
            flash('Please set your location in your profile to use this feature', 'warning')
            return redirect(url_for('profile'))
        return render_template('advance_mandi_analysis.html')
    except Exception as e:
        logger.error(f"Error in advance_mandi_analysis route: {str(e)}")
        flash('An error occurred while loading the page', 'error')
        return redirect(url_for('mandi_dashboard'))

@app.route('/api/advance-mandi/nearest-districts')
@login_required
def get_nearest_mandi_districts():
    """
    Get nearest districts based on user's location
    """
    try:
        if not current_user.is_authenticated:
            logger.warning("Unauthenticated user tried to access nearest districts")
            return jsonify({'error': 'User not authenticated'}), 401
            
        # Get user's coordinates
        latitude = current_user.latitude
        longitude = current_user.longitude
        
        if not latitude or not longitude:
            logger.warning(f"User {current_user.id} has no location set")
            return jsonify({'error': 'Location not set'}), 404
            
        logger.info(f"Finding nearest districts for user {current_user.id} at coordinates ({latitude}, {longitude})")
            
        # Import the function from advance_mandi_analysis module
        from models.advance_mandi_analysis import get_nearest_districts
        
        # Get nearest districts
        nearest_districts = get_nearest_districts(latitude, longitude)
        
        if not nearest_districts:
            logger.warning(f"No districts found for user {current_user.id}")
            return jsonify({'error': 'No districts found'}), 404
            
        logger.info(f"Found {len(nearest_districts)} nearest districts for user {current_user.id}")
        return jsonify(nearest_districts)
        
    except Exception as e:
        logger.error(f"Error in get_nearest_mandi_districts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advance-mandi/district-data')
@login_required
def get_advance_mandi_data():
    """
    Get mandi data for nearest districts with filters
    """
    try:
        # Get filters from request
        commodity = request.args.get('commodity')
        market = request.args.get('market')
        
        logger.info(f"Getting mandi data with filters - commodity: {commodity}, market: {market}")
        
        # Get user's coordinates
        if not current_user.is_authenticated:
            logger.warning("Unauthenticated user tried to access mandi data")
            return jsonify({'error': 'User not authenticated'}), 401
            
        latitude = current_user.latitude
        longitude = current_user.longitude
        
        if not latitude or not longitude:
            logger.warning(f"User {current_user.id} has no location set")
            return jsonify({'error': 'Location not set'}), 404
            
        # Import functions from advance_mandi_analysis module
        from models.advance_mandi_analysis import get_nearest_districts, get_mandi_data_for_districts
        
        # Get nearest districts
        nearest_districts = get_nearest_districts(latitude, longitude)
        
        if not nearest_districts:
            logger.warning(f"No districts found for user {current_user.id}")
            return jsonify({'error': 'No districts found'}), 404
            
        logger.info(f"Found {len(nearest_districts)} nearest districts for user {current_user.id}")
        
        # Get mandi data for these districts
        mandi_data = get_mandi_data_for_districts(nearest_districts, commodity, market)
        
        if not mandi_data:
            logger.warning(f"No mandi data found for districts: {[d['district_name'] for d in nearest_districts]}")
            return jsonify({'error': 'No mandi data found'}), 404
            
        logger.info(f"Found mandi data for {len(mandi_data['table_data'])} records")
        return jsonify(mandi_data)
        
    except Exception as e:
        logger.error(f"Error in get_advance_mandi_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/schemes')
@login_required
def schemes():
    with open('data/schemes_data.json', encoding='utf-8') as f:
        schemes_data = json.load(f)
    return render_template('schemes.html', schemes=schemes_data)

# Auction System Routes
@app.route('/farmer/crops')
@login_required
def my_crops():
    if current_user.user_role != 'farmer':
        flash('Access denied. This page is for farmers only.', 'error')
        return redirect(url_for('index'))
    
    # Get all crops with their highest bids and total bid counts
    crops = db.session.query(
        CropForSale,
        db.func.max(Bid.bid_amount).label('highest_bid'),
        db.func.count(Bid.id).label('total_bids')
    ).outerjoin(Bid).filter(
        CropForSale.farmer_id == current_user.id
    ).group_by(CropForSale.id).all()
    
    return render_template('farmer/my_crops.html', crops=crops)

# Define your allowed extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}

@app.route('/farmer/crops/add', methods=['GET', 'POST'])
@login_required
def add_crop():
    if request.method == 'POST':
        try:
            # Get form data
            commodity_id = request.form.get('commodity_id')
            quantity = request.form.get('quantity')
            unit = request.form.get('unit')
            base_price = request.form.get('base_price')
            district_id = request.form.get('district_id')
            expected_date = request.form.get('expected_date')
            description = request.form.get('description')
            
            # Handle image upload
            image_path = None
            if 'image' in request.files:
                image = request.files['image']
                # Create timestamp for unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                # Get file extension
                ext = image.filename.rsplit('.', 1)[1].lower()
                # Create filename with timestamp
                filename = f"{timestamp}_{secure_filename(image.filename)}"
                # Create the upload directory if it doesn't exist
                upload_dir = os.path.join(app.static_folder, 'crop_images')
                os.makedirs(upload_dir, exist_ok=True)
                # Save the file with forward slashes for consistency
                image_path = f"crop_images/{filename}"
                full_path = os.path.join(app.static_folder, image_path)
                image.save(full_path)
                print(f"Image saved to: {full_path}")  # Debug log
            
            # Create new crop
            new_crop = CropForSale(
                farmer_id=current_user.id,
                commodity_id=commodity_id,
                quantity=quantity,
                unit=unit,
                base_price=base_price,
                district_id=district_id,
                expected_date=datetime.strptime(expected_date, '%Y-%m-%d').date(),
                image_path=image_path,
                description=description
            )
            
            db.session.add(new_crop)
            db.session.commit()
            
            flash('Crop added successfully!', 'success')
            return redirect(url_for('my_crops'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding crop: {str(e)}")  # Debug log
            flash(f'Error adding crop: {str(e)}', 'error')
            return redirect(url_for('add_crop'))
    
    # Get commodities and districts for the form
    commodities = Commodity.query.all()
    districts = District.query.all()
    return render_template('farmer/add_crop.html', commodities=commodities, districts=districts)

@app.route('/dealer/crops')
@login_required
def available_crops():
    if current_user.user_role != 'dealer':
        flash('Access denied. This page is for dealers only.', 'error')
        return redirect(url_for('index'))
    
    # Get all active crops with their highest bids and total bid counts
    crops = db.session.query(
        CropForSale,
        db.func.max(Bid.bid_amount).label('highest_bid'),
        db.func.count(Bid.id).label('total_bids')
    ).outerjoin(Bid).filter(
        CropForSale.status == 'active'
    ).group_by(CropForSale.id).order_by(CropForSale.created_at.desc()).all()
    
    commodities = Commodity.query.order_by(Commodity.name).all()
    districts = District.query.order_by(District.name).all()
    
    return render_template('dealer/available_crops.html', 
                         crops=crops, 
                         commodities=commodities, 
                         districts=districts)

@app.route('/dealer/bids')
@login_required
def my_bids():
    if current_user.user_role != 'dealer':
        flash('Access denied. This page is for dealers only.', 'error')
        return redirect(url_for('index'))
    
    # Get all bids with their crop information and highest bid details
    bids = db.session.query(
        Bid,
        db.func.max(Bid.bid_amount).over(partition_by=Bid.crop_id).label('highest_bid'),
        db.func.count(Bid.id).over(partition_by=Bid.crop_id).label('total_bids')
    ).filter(
        Bid.dealer_id == current_user.id
    ).order_by(Bid.created_at.desc()).all()
    
    return render_template('dealer/my_bids.html', bids=bids)

@app.route('/dealer/active_crops')
@login_required
def active_crops():
    if current_user.user_role != 'dealer':
        flash('Only dealers can access this page', 'error')
        return redirect(url_for('index'))
    
    # Get all active crops with their highest bids
    crops = db.session.query(
        CropForSale,
        db.func.max(Bid.bid_amount).label('highest_bid'),
        db.func.count(Bid.id).label('total_bids')
    ).outerjoin(Bid).filter(
        CropForSale.status == 'active'
    ).group_by(CropForSale.id).all()
    
    return render_template('dealer/active_crops.html', crops=crops)

@app.route('/api/crops/<int:crop_id>/bid', methods=['POST'])
@login_required
def place_bid(crop_id):
    if current_user.user_role != 'dealer':
        return jsonify({'success': False, 'message': 'Only dealers can place bids'}), 403
    
    try:
        data = request.get_json()
        bid_amount = data.get('bid_amount')
        
        if not bid_amount or bid_amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid bid amount'}), 400
        
        # Get the crop
        crop = CropForSale.query.get_or_404(crop_id)
        
        if crop.status != 'active':
            return jsonify({'success': False, 'message': 'This auction is no longer active'}), 400
        
        # Get current highest bid
        current_highest_bid = Bid.query.filter_by(crop_id=crop_id, status='pending').order_by(Bid.bid_amount.desc()).first()
        
        # Check if bid is higher than current highest bid or base price
        min_bid = current_highest_bid.bid_amount if current_highest_bid else crop.base_price
        if bid_amount <= min_bid:
            return jsonify({'success': False, 'message': f'Bid must be higher than ₹{min_bid}'}), 400
        
        # Create new bid
        new_bid = Bid(
            crop_id=crop_id,
            dealer_id=current_user.id,
            bid_amount=bid_amount,
            status='pending'  # Initially set as pending
        )
        
        # If there was a previous highest bid, mark it as rejected
        if current_highest_bid:
            current_highest_bid.status = 'rejected'
        
        db.session.add(new_bid)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Bid placed successfully',
            'bid': {
                'id': new_bid.id,
                'amount': new_bid.bid_amount,
                'status': new_bid.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/crops/<int:crop_id>/bids', methods=['GET'])
@login_required
def get_crop_bids(crop_id):
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if crop exists for this user (farmer)
        cursor.execute("SELECT * FROM crops_for_sale WHERE id = %s AND farmer_id = %s", (crop_id, current_user.id))
        crop = cursor.fetchone()

        if not crop:
            return jsonify({
                'success': False,
                'message': 'Crop not found or access denied'
            }), 404

        # Fetch bids for this crop
        cursor.execute("""
            SELECT b.*, u.username as dealer_name 
            FROM bids b 
            JOIN users u ON b.dealer_id = u.id 
            WHERE b.crop_id = %s 
            ORDER BY b.created_at DESC
        """, (crop_id,))
        
        bids = cursor.fetchall()

        # Format response
        formatted_bids = []
        for bid in bids:
            formatted_bids.append({
                'bid_id': bid['id'],
                'bid_amount': float(bid['bid_amount']),
                'status': bid['status'],
                'created_at': bid['created_at'].isoformat(),
                'dealer_name': bid['dealer_name'],
                'dealer_id': bid['dealer_id']
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'crop_id': crop_id,
            'bids': formatted_bids
        })

    except Exception as e:
        print(f"Error fetching bids: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/crops/<int:crop_id>/close', methods=['POST'])
@login_required
def close_auction(crop_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if crop belongs to the current farmer
        cursor.execute("SELECT * FROM crops_for_sale WHERE id = %s AND farmer_id = %s", (crop_id, current_user.id))
        crop = cursor.fetchone()

        if not crop:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        # Get highest bid with dealer info
        cursor.execute("""
            SELECT b.*, u.username AS dealer_name, u.email AS dealer_email
            FROM bids b
            JOIN users u ON b.dealer_id = u.id
            WHERE b.crop_id = %s
            ORDER BY b.bid_amount DESC
            LIMIT 1
        """, (crop_id,))
        winning_bid = cursor.fetchone()

        if winning_bid:
            # Reject all bids
            cursor.execute("UPDATE bids SET status = 'rejected' WHERE crop_id = %s", (crop_id,))
            
            # Accept the highest bid
            cursor.execute("UPDATE bids SET status = 'accepted' WHERE id = %s", (winning_bid['id'],))

        # Mark the crop as SOLD in all cases
        cursor.execute("UPDATE crops_for_sale SET status = 'sold' WHERE id = %s", (crop_id,))
        conn.commit()

        if winning_bid:
            return jsonify({
                'success': True,
                'message': 'Auction closed successfully',
                'dealer_details': {
                    'name': winning_bid['dealer_name'],
                    'email': winning_bid['dealer_email'],
                    'bid_amount': float(winning_bid['bid_amount']),
                    'bid_date': winning_bid['created_at'].strftime('%d %b %Y')
                }
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Auction closed successfully. No bids were placed.'
            })

    except Exception as e:
        conn.rollback()
        print("Error closing auction:", str(e))
        return jsonify({'success': False, 'message': 'Error closing auction.'}), 500

    finally:
        cursor.close()
        conn.close()



@app.route('/api/crops/<int:crop_id>/highest-bid')
@login_required
def get_highest_bid(crop_id):
    crop = CropForSale.query.get_or_404(crop_id)
    highest_bid = Bid.query.filter_by(crop_id=crop_id).order_by(Bid.bid_amount.desc()).first()
    
    return jsonify({
        'highest_bid': highest_bid.bid_amount if highest_bid else None,
        'base_price': crop.base_price
    })

@app.route('/api/bids/<int:bid_id>', methods=['GET', 'PUT'])
@login_required
def manage_bid(bid_id):
    bid = Bid.query.get_or_404(bid_id)
    if bid.dealer_id != current_user.id and current_user.user_role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if request.method == 'GET':
        return jsonify({
            'id': bid.id,
            'bid_amount': bid.bid_amount,
            'status': bid.status,
            'crop': {
                'id': bid.crop.id,
                'commodity_name': bid.crop.commodity.name,
                'base_price': bid.crop.base_price,
                'highest_bid': bid.crop.highest_bid
            }
        })
    
    # PUT request to update bid
    if bid.status != 'active':
        return jsonify({'success': False, 'message': 'Cannot update non-active bid'}), 400
    
    data = request.get_json()
    new_amount = float(data.get('bid_amount', 0))
    
    if new_amount <= bid.crop.base_price:
        return jsonify({'success': False, 'message': 'Bid amount must be higher than base price'}), 400
    
    # Check if this is the highest bid
    highest_bid = Bid.query.filter(
        Bid.crop_id == bid.crop_id,
        Bid.id != bid.id
    ).order_by(Bid.bid_amount.desc()).first()
    
    if highest_bid and new_amount <= highest_bid.bid_amount:
        return jsonify({'success': False, 'message': 'Bid amount must be higher than current highest bid'}), 400
    
    bid.bid_amount = new_amount
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Bid updated successfully'})

# Helper function for file uploads
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/api/crops/<int:crop_id>', methods=['DELETE'])
@login_required
def delete_crop(crop_id):
    try:
        crop = CropForSale.query.get_or_404(crop_id)
        
        # Check if user owns the crop
        if crop.farmer_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Delete associated image if exists
        if crop.image_path:
            image_path = os.path.join('static', crop.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete associated bids
        Bid.query.filter_by(crop_id=crop_id).delete()
        
        # Delete crop
        db.session.delete(crop)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(debug=True) 