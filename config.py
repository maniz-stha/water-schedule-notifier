import os

def load_env_file(filepath=".env"):
    """Load key-value pairs from a .env file into os.environ if it exists."""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

def load_config(env_file=".env"):
    """Load and validate credentials from the environment."""
    if env_file:
        load_env_file(env_file)
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    missing = []
    if not bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not chat_id:
        missing.append("TELEGRAM_CHAT_ID")
        
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
    return {
        "TELEGRAM_BOT_TOKEN": bot_token,
        "TELEGRAM_CHAT_ID": chat_id
    }

def load_ai_config(env_file=".env"):
    """Load and validate AI credentials from the environment."""
    if env_file:
        load_env_file(env_file)
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("Missing required environment variable: GEMINI_API_KEY")
    return {
        "GEMINI_API_KEY": gemini_api_key,
        "GEMINI_MODEL": os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    }

