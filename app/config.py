import os

# Feature flags for optional AI models with graceful fallbacks
AI_CONFIG = {
    # Demand Forecasting: Chronos-Bolt-tiny -> Prophet -> Rule-based Hourly Average Fallback
    "ENABLE_CHRONOS_DEMAND": os.getenv("ENABLE_CHRONOS_DEMAND", "true").lower() in ("true", "1", "yes"),
    
    # Voice Booking via Browser Web Speech API + Natural Language Parser
    "ENABLE_VOICE_BOOKING": os.getenv("ENABLE_VOICE_BOOKING", "true").lower() in ("true", "1", "yes"),
    
    # Number Plate OCR: EasyOCR -> Regex-only Fallback
    "ENABLE_EASYOCR": os.getenv("ENABLE_EASYOCR", "true").lower() in ("true", "1", "yes"),
    
    # Face Match: DeepFace / CV2 Feature Match -> Verification Fallback
    "ENABLE_FACEMATCH": os.getenv("ENABLE_FACEMATCH", "true").lower() in ("true", "1", "yes"),
    
    # Semantic Place Search: sentence-transformers (all-MiniLM-L6-v2) -> Fuzzy Gazetteer Fallback
    "ENABLE_SEMANTIC_SEARCH": os.getenv("ENABLE_SEMANTIC_SEARCH", "true").lower() in ("true", "1", "yes"),
    
    # Strict execution timeout for ML model inference
    "MODEL_TIMEOUT_SECONDS": float(os.getenv("MODEL_TIMEOUT_SECONDS", "5.0"))
}


def get_ai_config():
    return AI_CONFIG
