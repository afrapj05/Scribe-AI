#!/usr/bin/env python3
"""
Installation and setup script for enhanced ScribeAI with SQL database,
multilingual support, and advanced audio processing.
"""

import subprocess
import sys
import os

def install_packages():
    """Install all required packages."""
    print("📦 Installing required packages...")
    
    packages = [
        'sqlalchemy==2.0.23',
        'psycopg2-binary==2.9.9',
        'noisereduce==3.0.0',
        'python-dotenv==1.0.0',
        'sounddevice==0.4.5',
    ]
    
    for package in packages:
        print(f"  Installing {package}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', package])
    
    print("✅ All packages installed successfully!")


def initialize_database():
    """Initialize the SQL database."""
    print("\n🗄️ Initializing SQL database...")
    
    try:
        from database import init_db
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    return True


def create_env_file():
    """Create .env file with configuration."""
    print("\n⚙️ Creating configuration file...")
    
    env_content = """# ScribeAI Configuration

# Database Configuration
# Options: 'sqlite' or 'postgresql'
DB_TYPE=sqlite

# For SQLite (local development)
DATABASE_URL=sqlite:///clinical_records.db

# For PostgreSQL (production)
# DATABASE_URL=postgresql://user:password@localhost:5432/clinical_db

# Audio Configuration
SAMPLE_RATE=44100
AUDIO_CHANNELS=1

# Multilingual
DEFAULT_LANGUAGE=en

# OpenAI Whisper
WHISPER_MODEL=base

# Ollama
OLLAMA_MODEL=cniongolo/biomistral
OLLAMA_BASE_URL=http://localhost:11434
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
    else:
        print("⚠️ .env file already exists. Skipping...")


def print_setup_complete():
    """Print setup completion message."""
    print("\n" + "="*60)
    print("✅ ScribeAI Enhanced Setup Complete!")
    print("="*60)
    print("""
NEW FEATURES:
  🗄️  SQL Database (SQLite/PostgreSQL)
  🌍 Multilingual Support (8 languages)
  🎙️ Unlimited Audio Recording
  🔊 Advanced Noise Filtering (4 methods)
  📊 Enhanced Analytics & Reporting
  
NEXT STEPS:
  1. Start Ollama service:
     $ ollama serve
  
  2. Pull BioMistral model:
     $ ollama pull cniongolo/biomistral
  
  3. Run the application:
     $ streamlit run app.py
  
DATABASE:
  - Type: SQLite/PostgreSQL (configurable)
  - Location: clinical_records.db (SQLite)
  - Tables: patients, visits, soap_notes, audio_recordings, prescriptions, users
  
AUDIO FILTERS AVAILABLE:
  - Band-pass (80-6000 Hz): Optimal for speech
  - Low-pass (6000 Hz): General noise reduction
  - High-pass (80 Hz): Rumble removal
  - Advanced: noisereduce library (requires librosa)
  
SUPPORTED LANGUAGES:
  - 🇬🇧 English
  - 🇪🇸 Spanish
  - 🇫🇷 French
  - 🇩🇪 German
  - 🇮🇳 Hindi
  - 🇨🇳 Chinese
  - 🇵🇹 Portuguese
  - 🇸🇦 Arabic

DOCUMENTATION:
  - See README.md for comprehensive guide
  - Check QUICKSTART.py for examples
  - Review database.py for schema details
  - Check audio_processor.py for audio methods
  - See translations.py for multilingual strings

SUPPORT:
  For issues or feature requests, refer to documentation files.
""")


if __name__ == "__main__":
    print("🚀 ScribeAI Enhanced Installation Setup\n")
    
    try:
        install_packages()
        create_env_file()
        
        if initialize_database():
            print_setup_complete()
            print("✨ Ready to use ScribeAI Enhanced!")
        else:
            print("⚠️ Database initialization failed. Please check configuration.")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
