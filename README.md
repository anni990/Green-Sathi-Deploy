# AI Green Sathi - AI Farming Assistant

A multilingual AI chatbot for Indian farmers providing agricultural advice, plant disease diagnosis, and soil report analysis through voice, text, and image interactions.

![Error in loading image](static/images/home-page.png)

## Features

- **Multilingual Support**: Chat in Hindi, English, Bhojpuri, Bundelkhandi, Marathi, and Haryanvi
- **Voice Interaction**: Speak to the AI and get voice responses
- **Plant Disease Detection**: Upload plant images for disease identification and treatment recommendations
- **Soil Report Analysis**: Upload soil test reports for crop and fertilizer recommendations
- **Animated Character**: Interactive AI character that responds visually to your questions
- **Mobile-Friendly**: Responsive design works well on smartphones and tablets
- **Secure Authentication**: User account management with data persistence

## Tech Stack

- **Frontend**: HTML, Tailwind CSS, JavaScript (with GSAP animations)
- **Backend**: Flask (Python)
- **STT**: OpenAI Whisper
- **TTS**: Coqui TTS
- **NLP (Q&A)**: HuggingFace Models (google/mt5-base)
- **Image Model**: HuggingFace plant disease model
- **Soil Parsing**: LayoutParser + Tesseract OCR
- **Database**: MySQL
- **Character UI**: JavaScript + GSAP

## Installation

### Prerequisites

- Python 3.8+
- MySQL
- Tesseract OCR
- CUDA-compatible GPU (optional, for faster inference)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/farmer-ai-assistant.git
   cd farmer-ai-assistant
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install Tesseract OCR:
   - Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt install tesseract-ocr`
   - macOS: `brew install tesseract`

4. Create database schema:
   ```bash
   # Log into MySQL
   mysql -u root -p
   
   # Execute the SQL schema (or import through phpMyAdmin)
   source database_schema.sql
   ```

5. Configure environment variables:
   - Create a `.env` file based on the provided example
   - Add your API keys for OpenAI and HuggingFace
   - Update database credentials

   ```
   SECRET_KEY=your_secret_key_here
   DATABASE_URL=mysql://username:password@localhost/farmers_chatbot
   OPENAI_API_KEY=your_openai_api_key_here
   HUGGINGFACE_API_KEY=your_huggingface_api_key_here
   TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe  # Windows path example
   ```

## Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Access the web application in your browser:
   ```
   http://127.0.0.1:5000
   ```

## API Endpoints

The application provides the following API endpoints:

- `/api/process_text` - Process text input
- `/api/process_voice` - Process voice input
- `/api/process_image` - Process plant image for disease detection
- `/api/process_soil_report` - Process soil report for analysis

## External API Requirements

1. **OpenAI API Key** (for Whisper STT)
   - Obtain from [OpenAI Platform](https://platform.openai.com/)
   - Alternatively, get from [OpenRouter](https://openrouter.ai/)

2. **HuggingFace API Key** (for NLP and image models)
   - Obtain from [HuggingFace](https://huggingface.co/settings/tokens)

## Directory Structure

```
.
├── app.py                  # Main Flask application
├── database_schema.sql     # SQL schema for MySQL
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── static/                 # Static files
│   ├── css/                # CSS assets
│   ├── js/                 # JavaScript assets
│   ├── images/             # Image assets
│   └── uploads/            # User uploaded files
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Landing page
│   ├── chat.html           # Main chat interface
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── profile.html        # User profile page
│   └── history.html        # Chat history page
└── models/                 # ML model handlers
    ├── chat_model.py       # Chat processing logic
    ├── speech_handler.py   # STT and TTS processing
    ├── image_diagnosis.py  # Plant disease detection
    └── soil_report.py      # Soil report processing
```

## Development

### Testing Without API Keys

The application provides fallback methods to run without API keys for development purposes:

- Chat model uses rule-based responses
- Image diagnosis uses mock detection based on image properties
- Soil analysis works with example values

### Adding More Languages

To add support for more Indian languages:

1. Add the language entry to the `LANGUAGE_CODES` dictionary in both:
   - `models/chat_model.py`
   - `models/speech_handler.py`

2. Update the language options in the HTML templates.

## Fertilizer Recommendation Report PDF Generation

The fertilizer recommendation feature includes PDF generation which requires wkhtmltopdf to be installed on your system:

### Installing wkhtmltopdf

#### Windows
1. Download the installer from the [official wkhtmltopdf website](https://wkhtmltopdf.org/downloads.html)
2. Run the installer with default options
3. Make sure to add the installation directory to your system PATH or configure it in the app

#### Linux (Ubuntu/Debian)
```
sudo apt-get update
sudo apt-get install -y wkhtmltopdf
```

#### macOS
```
brew install --cask wkhtmltopdf
```

After installation, the PDF generation feature should work automatically with the application.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- HuggingFace for providing free model access
- OpenRouter for affordable API access to large language models
- Coqui TTS for open-source text-to-speech
- OpenAI for the Whisper STT model
- The open source community for various libraries and tools

---

Created for helping Indian farmers access AI-powered agricultural advice in their native languages. 
