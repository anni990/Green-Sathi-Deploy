import os
import numpy as np
import torch
import torchaudio
from pathlib import Path
import soundfile as sf
import librosa
import tempfile
import warnings
import traceback  # Add traceback for better error logging
from gtts import gTTS
import time
import subprocess  # For direct ffmpeg calls
import shutil  # For file operations
import wave  # Standard library for WAV files
import speech_recognition as sr
# Try to import additional libraries for conversion
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Pydub not available. Some audio conversions may fail.")

# Suppress warnings
warnings.filterwarnings("ignore")

AudioSegment.converter = r"C:\ffmpeg-2025-04-21-git-9e1162bdf1-full_build\bin\ffmpeg.exe"
AudioSegment.ffprobe   = r"C:\ffmpeg-2025-04-21-git-9e1162bdf1-full_build\bin\ffprobe.exe"

# Language mappings
LANGUAGE_CODES = {
    'english': 'en',
    'hindi': 'hi',
    'bhojpuri': 'hi',  # Use Hindi as fallback 
    'bundelkhandi': 'hi',  # Use Hindi as fallback
    'marathi': 'mr',
    'haryanvi': 'hi',  # Use Hindi as fallback
    'bengali': 'bn',
    'tamil': 'ta',
    'telugu': 'te',
    'kannada': 'kn',
    'gujarati': 'gu',
    'urdu': 'ur',
    'malayalam': 'ml',
    'punjabi': 'pa'
}

# Speech Recognition language codes (more specific with region)
STT_LANGUAGE_CODES = {
    'english': 'en-IN',
    'hindi': 'hi-IN',
    'bhojpuri': 'hi-IN',  # Use Hindi as fallback
    'bundelkhandi': 'hi-IN',  # Use Hindi as fallback
    'marathi': 'mr-IN',
    'haryanvi': 'hi-IN',  # Use Hindi as fallback
    'bengali': 'bn-IN',
    'tamil': 'ta-IN',
    'telugu': 'te-IN',
    'kannada': 'kn-IN',
    'gujarati': 'gu-IN',
    'urdu': 'ur-IN',
    'malayalam': 'ml-IN',
    'punjabi': 'pa-IN'
}

device = "cuda" if torch.cuda.is_available() else "cpu"

# model_whisper = whisper.load_model("small", device=device)

# Cache for models
_whisper_model = None
_tts_models = {}

# Check if CUDA is available


# Constants
SAMPLE_RATE = 16000
DEFAULT_ERROR_AUDIO = "static/audio/error_message.mp3"

# Check if ffmpeg is available and print clear installation instructions if not
def is_ffmpeg_available():
    """Check if ffmpeg is available on the system"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return True
        else:
            print("FFmpeg command found but returned an error.")
            return False
    except (subprocess.SubprocessError, FileNotFoundError):
        print("""
FFmpeg not found. To install FFmpeg:
1. Windows: Download from https://www.gyan.dev/ffmpeg/builds/ and add to PATH
2. macOS: Use 'brew install ffmpeg'
3. Linux: Use 'apt-get install ffmpeg' or your distro's package manager
After installing, restart your application.
""")
        return False

# Fix Windows path issues
def normalize_path(path):
    """Convert path to proper format for cross-platform compatibility"""
    if path is None:
        return None
        
    # Convert to string if Path object
    if isinstance(path, Path):
        path = str(path)
        
    # Replace backslashes with forward slashes
    path = path.replace('\\', '/')
    
    # Make absolute path if needed
    if not os.path.isabs(path):
        path = os.path.abspath(path)
        
    # Convert to forward slashes again after making absolute
    path = path.replace('\\', '/')
    
    return path


def ensure_error_audio_exists():
    """Create a default error audio file if it doesn't exist."""
    error_file = Path(DEFAULT_ERROR_AUDIO)
    if not error_file.exists():
        try:
            # Create error messages in multiple languages
            error_messages = {
                'en': "Sorry, there was an error processing your audio.",
                'hi': "क्षमा करें, आपके ऑडियो को प्रोसेस करने में एक त्रुटि हुई है।",
                'bn': "দুঃখিত, আপনার অডিও প্রসেস করার সময় একটি ত্রুটি হয়েছে।",
                'mr': "क्षमा करा, आपल्या ऑडिओवर प्रक्रिया करताना एक त्रुटी झाली आहे।",
                'ta': "மன்னிக்கவும், உங்கள் ஆடியோவை செயலாக்குவதில் பிழை ஏற்பட்டது.",
                'te': "క్షమించండి, మీ ఆడియోను ప్రాసెస్ చేయడంలో లోపం ఉంది.",
                'kn': "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಆಡಿಯೊವನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸುವಲ್ಲಿ ದೋಷ ಉಂಟಾಗಿದೆ.",
                'gu': "માફ કરશો, તમારી ઓડિયો પ્રોસેસ કરવામાં ભૂલ આવી.",
                'ur': "معذرت، آپ کی آڈیو پر کارروائی کرنے میں ایک خرابی پیش آئی۔",
                'ml': "ക്ഷമിക്കണം, നിങ്ങളുടെ ഓഡിയോ പ്രോസസ്സ് ചെയ്യുന്നതിൽ ഒരു പിശക് സംഭവിച്ചു.",
                'pa': "ਮਾਫ ਕਰਨਾ, ਤੁਹਾਡੇ ਆਡੀਓ ਨੂੰ ਪ੍ਰੋਸੈਸ ਕਰਨ ਵਿੱਚ ਇੱਕ ਗਲਤੀ ਹੋਈ ਹੈ।"
            }
            
            # Create directory if it doesn't exist
            error_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate TTS for Hindi error message (default)
            tts = gTTS(error_messages['hi'], lang='hi')  # Use Hindi as default
            tts.save(str(error_file))
            print(f"Created default error audio at {error_file}")
        except Exception as e:
            print(f"Failed to create default error audio: {e}")

# Call this function at module import time
ensure_error_audio_exists()

def convert_with_pydub_no_ffmpeg(input_path, output_path):
    """
    Convert audio file to WAV using pydub without relying on ffmpeg
    
    Args:
        input_path: Path to input audio file
        output_path: Path to output WAV file
        
    Returns:
        bool: True if conversion was successful
    """
    if not PYDUB_AVAILABLE:
        print("Pydub is not available for conversion")
        return False
        
    try:
        # Normalize paths
        input_path = normalize_path(input_path)
        output_path = normalize_path(output_path)
        
        print(f"Attempting pydub conversion from {input_path} to {output_path}")
        
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f"Input file does not exist for pydub: {input_path}")
            return False
        
        # Set pydub to explicitly not use ffmpeg
        from pydub import AudioSegment
        AudioSegment.converter = None  # Don't use external converter
        
        # Try several import methods
        try:
            # Method 1: Direct load with explicit format
            audio = AudioSegment.from_file(input_path, format="webm")
            print("Successfully loaded WebM with pydub")
        except Exception as e1:
            try:
                # Method 2: Try as MP3
                audio = AudioSegment.from_mp3(input_path)
                print("Successfully loaded as MP3 with pydub")
            except Exception as e2:
                try:
                    # Method 3: Try as WAV
                    audio = AudioSegment.from_wav(input_path)
                    print("Successfully loaded as WAV with pydub")
                except Exception as e3:
                    try:
                        # Method 4: Auto-detect format
                        audio = AudioSegment.from_file(input_path)
                        print("Successfully loaded with pydub auto-detection")
                    except Exception as e4:
                        print(f"All pydub loading methods failed: {e1}, {e2}, {e3}, {e4}")
                        return False
        
        # Set the frame rate
        audio = audio.set_frame_rate(SAMPLE_RATE)
        
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(1)
            
        # Export as WAV using pydub's built-in WAV exporter (not relying on ffmpeg)
        audio.export(output_path, format="wav")
        
        # Verify the file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"Successfully converted to WAV using pydub: {output_path}")
            return True
            
        print(f"Pydub output file verification failed: exists={os.path.exists(output_path)}, size={os.path.getsize(output_path) if os.path.exists(output_path) else 0}")
        return False
    except Exception as e:
        print(f"Error converting with pydub: {traceback.format_exc()}")
        return False


def convert_with_librosa(input_path, output_path):
    """
    Convert audio file to WAV using librosa (pure Python solution)
    
    Args:
        input_path: Path to input audio file
        output_path: Path to output WAV file
        
    Returns:
        bool: True if conversion was successful
    """
    try:
        # Normalize paths
        input_path = normalize_path(input_path)
        output_path = normalize_path(output_path)
        
        print(f"Attempting librosa conversion from {input_path} to {output_path}")
        
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f"Input file does not exist for librosa: {input_path}")
            return False
            
        # Load file with librosa
        try:
            y, sr = librosa.load(input_path, sr=SAMPLE_RATE, mono=True)
            print(f"Successfully loaded audio with librosa, shape: {y.shape}")
            
            # Save as WAV using soundfile
            sf.write(output_path, y, SAMPLE_RATE)
            
            # Verify the file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Successfully converted to WAV using librosa+soundfile: {output_path}")
                return True
                
            print(f"Librosa output file verification failed")
            return False
        except Exception as e:
            print(f"Error in librosa conversion: {e}")
            return False
    except Exception as e:
        print(f"Error with librosa: {traceback.format_exc()}")
        return False

def convert_with_torchaudio(input_path, output_path):
    """
    Convert audio file to WAV using torchaudio (backend independent)
    
    Args:
        input_path: Path to input audio file
        output_path: Path to output WAV file
        
    Returns:
        bool: True if conversion was successful
    """
    try:
        # Normalize paths
        input_path = normalize_path(input_path)
        output_path = normalize_path(output_path)
        
        print(f"Attempting torchaudio conversion from {input_path} to {output_path}")
        
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f"Input file does not exist for torchaudio: {input_path}")
            return False
            
        # Various backends to try
        backends_to_try = ["sox_io", "soundfile", "default"]
        succeed = False
        
        for backend in backends_to_try:
            if succeed:
                break
                
            try:
                # Set backend if available
                try:
                    torchaudio.set_audio_backend(backend)
                    print(f"Using torchaudio backend: {backend}")
                except Exception as be:
                    print(f"Couldn't set torchaudio backend {backend}: {be}")
                    continue
                
                # Try to load with torchaudio
                try:
                    # With format hint
                    waveform, sample_rate = torchaudio.load(input_path, format="webm")
                except Exception:
                    # Without format hint
                    waveform, sample_rate = torchaudio.load(input_path)
                
                # Convert to mono if needed
                if waveform.shape[0] > 1:
                    waveform = torch.mean(waveform, dim=0, keepdim=True)
                
                # Resample if needed
                if sample_rate != SAMPLE_RATE:
                    resampler = torchaudio.transforms.Resample(sample_rate, SAMPLE_RATE)
                    waveform = resampler(waveform)
                
                # Save as WAV
                torchaudio.save(output_path, waveform, SAMPLE_RATE, format="wav")
                
                # Verify the file was created
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"Successfully converted to WAV using torchaudio ({backend}): {output_path}")
                    succeed = True
                    break
                    
                print(f"Torchaudio output file verification failed with backend {backend}")
            except Exception as e:
                print(f"Error in torchaudio conversion with backend {backend}: {e}")
        
        return succeed
    except Exception as e:
        print(f"Error with torchaudio: {traceback.format_exc()}")
        return False

def copy_to_wav_if_missing_extension(input_path, output_dir):
    """
    Some audio files might be missing extensions but are actually WAV.
    This function checks and copies them with a .wav extension.
    
    Returns:
        Path to a wav file or None if not a valid audio file
    """
    try:
        # Normalize paths
        input_path = Path(normalize_path(input_path))
        output_dir = normalize_path(output_dir)
        
        # If already has .wav extension, just return
        if input_path.suffix.lower() == '.wav':
            return str(input_path)
            
        # If no extension or unknown extension, try to copy as WAV
        if not input_path.suffix or input_path.suffix.lower() not in ['.mp3', '.ogg', '.webm', '.m4a', '.mp4']:
            # Create new path with .wav extension
            new_path = Path(output_dir) / f"{input_path.stem}.wav"
            
            # Simply copy the file
            shutil.copy2(str(input_path), str(new_path))
            
            # Verify it's valid by trying to open it
            try:
                data, sr = sf.read(str(new_path), frames=1000)  # Just read a small part
                print(f"Successfully copied to WAV: {new_path}")
                return str(new_path)
            except Exception:
                # Not a valid WAV, delete the copy
                if new_path.exists():
                    new_path.unlink()
                return None
        
        return None
    except Exception as e:
        print(f"Error copying to wav: {traceback.format_exc()}")
        return None

def save_as_wave_directly(audio_data, sample_rate, output_path):
    """
    Save audio data as WAV using the wave module (standard library)
    
    Args:
        audio_data: NumPy array of audio samples
        sample_rate: Sampling rate
        output_path: Path to save the WAV file
        
    Returns:
        bool: True if successful
    """
    try:
        # Normalize path
        output_path = normalize_path(output_path)
        
        # Ensure audio_data is scaled properly for 16-bit PCM
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Convert to 16-bit PCM
        samples = (audio_data * 32767).astype(np.int16)
        
        # Open WAV file
        with wave.open(output_path, 'wb') as wav_file:
            # Set parameters (1 channel, 2 bytes per sample, 16000 Hz)
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes = 16 bits
            wav_file.setframerate(sample_rate)
            
            # Write the data
            wav_file.writeframes(samples.tobytes())
        
        # Verify the file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"Successfully saved WAV using wave module: {output_path}")
            return True
            
        print(f"Wave module output file verification failed")
        return False
    except Exception as e:
        print(f"Error saving as wave: {traceback.format_exc()}")
        return False

def convert_with_ffmpeg(input_path, output_path):
    try:
        # ✅ Convert webm to wav (mono, 16kHz)
        audio = AudioSegment.from_file(input_path, format="webm")
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        print(f"[Conversion Error] {e}")
        return False
    

def preprocess_audio(audio_file_path):
    """
    Preprocess audio file for speech recognition.
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Path to the preprocessed audio file
    """
    # try:
    # Convert string path to Path object for better handling
    audio_path = Path(normalize_path(audio_file_path))
    
    print(f"Preprocessing audio file: {audio_path}")
    
    # Check if file exists
    if not audio_path.exists():
        print(f"Audio file not found: {audio_path}")
        return None
        
    # Check if file is empty
    if audio_path.stat().st_size == 0:
        print(f"Audio file is empty: {audio_path}")
        return None
    
    # Create a temporary directory for processed audio
    temp_dir = Path(tempfile.mkdtemp())
    processed_file = temp_dir / f"processed_{int(time.time())}.wav"

    # For WebM files, try multiple conversion methods
    converted = False
    
    if audio_path.suffix.lower() == '.webm' or audio_path.suffix.lower() == '.mp3' or audio_path.suffix.lower() == '.m4a' or audio_path.suffix.lower() == '.ogg':
        print(f"Attempting to convert audio file: {audio_path}")
        
        # Method 1: Try ffmpeg (No FFmpeg dependency)
        if not converted:
            temp_wav = temp_dir / f"temp_ffmpeg_{int(time.time())}.wav"
            if convert_with_ffmpeg(audio_path, temp_wav):
                audio_path = temp_wav
                converted = True
                print(f"Successfully converted to WAV using ffmpeg: {audio_path}")

                return audio_path
        
        # Method 2: Try Librosa (consistent library)
        if not converted:
            temp_wav = temp_dir / f"temp_librosa_{int(time.time())}.wav"
            if convert_with_librosa(audio_path, temp_wav):
                audio_path = temp_wav
                converted = True
                print(f"Successfully converted to WAV using librosa: {audio_path}")
        
        # Method 3: Try TorchAudio backends
        if not converted:
            temp_wav = temp_dir / f"temp_torchaudio_{int(time.time())}.wav"
            if convert_with_torchaudio(audio_path, temp_wav):
                audio_path = temp_wav
                converted = True
                print(f"Successfully converted to WAV using torchaudio: {audio_path}")
        
        # Method 4: Try pydub without FFmpeg
        if not converted and PYDUB_AVAILABLE:
            temp_wav = temp_dir / f"temp_pydub_{int(time.time())}.wav"
            if convert_with_pydub_no_ffmpeg(audio_path, temp_wav):
                audio_path = temp_wav
                converted = True
                print(f"Successfully converted to WAV using pydub: {audio_path}")
        
        # Method 5: Try direct copy if file might actually be WAV with wrong extension
        if not converted:
            copied_wav = copy_to_wav_if_missing_extension(audio_path, temp_dir)
            if copied_wav:
                audio_path = Path(copied_wav)
                converted = True
                print(f"Treating file as WAV with wrong extension: {audio_path}")
                
        # If all methods failed, log detailed error
        if not converted:
            print(f"All audio conversion methods failed for: {audio_path}")


def speech_to_text(audio_file_path, language="en-IN"):
    """
    Convert speech to text.
    
    Args:
        audio_file_path: Path to the audio file
        language: Language code or name ("en", "hi", "english", "hindi")
        
    Returns:
        Transcribed text
    """

    try:
        # Convert language name to ISO code if needed
        lang_code = STT_LANGUAGE_CODES.get(language.lower(), language)
        
        # Normalize and check input path
        audio_file_path = normalize_path(audio_file_path)
        if not os.path.exists(audio_file_path):
            print(f"Audio file not found for STT: {audio_file_path}")
            error_msg = "Audio file not found" if lang_code.startswith("en") else "ऑडियो फ़ाइल नहीं मिली"
            return f"[{error_msg}]"
        
        print(audio_file_path)

        # Preprocess audio file
        processed_audio = preprocess_audio(audio_file_path)
        print(processed_audio)

        processed_audio = str(processed_audio).replace('\\', '/')
        print(processed_audio)

        # Use whisper model
        # try:
        #     if model_whisper:
        #         result = model_whisper.transcribe(processed_audio, language=lang_code)
        #         transcription = result["text"].strip()
        #         print("transcription of whisper model", transcription)
        #         return transcription
        # except Exception as e:
        #     print(f"Error in whisper model: {e}")

        # Use Google Speech Recognition API
        r = sr.Recognizer()
        try:
            with sr.AudioFile(processed_audio) as source:
                audio = r.record(source)  # listen to the entire file
            text = r.recognize_google(audio, language=lang_code)
            print("text of google speech recognition", text)
            return text
        except sr.UnknownValueError:
            return "❌ Could not understand the audio"
        except sr.RequestError as e:
            return f"❌ Request Error: {e}"

    except Exception as e:
        print(f"Unexpected error in speech_to_text: {traceback.format_exc()}")
        error_msg = "Audio processing error" if language.startswith("en") else "ऑडियो प्रोसेसिंग त्रुटि"
        return f"[{error_msg}]"

def text_to_speech(text, language="en"):
    """
    Convert text to speech.
    
    Args:
        text: Text to convert to speech
        language: Language code or name ("en", "hi", "english", "hindi")
        
    Returns:
        Path to the audio file
    """
    try:
        # Convert language name to ISO code for gTTS
        lang_code = LANGUAGE_CODES.get(language.lower(), language)
        print(f"Using language code '{lang_code}' for TTS")
        
        # Create a temporary file for the audio
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # go back to parent directory of base_dir
        base_dir = os.path.dirname(base_dir)
        audio_file = os.path.join(base_dir, 'static', 'storage', 'tts_' + str(int(time.time())) + '.mp3')
        
        print(text)
        print(type(text))
        # Text preprocessing (removing ∗ asterisk characters from the give text)
        text = text.replace("∗", "")
        print(text)
        print(type(text))

        # Convert text to speech using gTTS with correct language code
        try:
            tts = gTTS(text, lang=lang_code, tld="co.in")
            tts.save(str(audio_file))
            print(audio_file)
            
        except ValueError as e:
            # Handle unsupported language
            print(f"Language '{lang_code}' not supported by gTTS: {e}")
            # Fall back to English if specified language is not supported
            print("Falling back to English TTS")
            tts = gTTS(text, lang='en')
            tts.save(str(audio_file))
        
        # Verify the file was created successfully
        # if not audio_file.exists() or audio_file.stat().st_size == 0:
        #     print(f"Failed to create TTS audio file")
        #     return DEFAULT_ERROR_AUDIO

        # audio_url = file:///D:/1.%20Inventohack%20Internship/2.%20AI%20Chatbot%20for%20Farmers/Testing/static/storage/tts_1745416644.mp3
        # response_audio_url = static/storage/tts_1745416644.mp3

        # trim path to static/storage/tts_1745416644.mp3
        audio_file = audio_file.split('static')[1]
        response_audio_url = "static" + audio_file
        

        # Make sure the audio file path uses forward slashes for URLs
        return str(response_audio_url).replace('\\', '/')
        
    except Exception as e:
        print(f"Error in text_to_speech: {traceback.format_exc()}")
        return DEFAULT_ERROR_AUDIO

# Backward compatibility functions
def convert_audio_to_wav(input_path):
    """Convert audio to WAV format using librosa"""
    try:
        input_path = Path(normalize_path(input_path))
        
        if not input_path.exists():
            print(f"File not found for conversion: {input_path}")
            return str(input_path)
            
        if input_path.suffix.lower() == '.wav':
            return str(input_path)
            
        # Load audio
        y, sr = librosa.load(str(input_path), sr=16000)
        
        # Create output path
        output_path = input_path.with_suffix('.wav')
        
        # Save as WAV
        sf.write(str(output_path), y, sr)
        
        return str(output_path)
    except Exception as e:
        print(f"Error converting audio to WAV: {traceback.format_exc()}")
        return str(input_path) 