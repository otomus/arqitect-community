import json
from textblob import TextBlob

def personality_voice_rewriter(message: str, target_personality: str) -> str:
    """
    Rewrites messages to match a specified personality tone without translating the content.
    """
    try:
        # Analyze the sentiment of the message
        blob = TextBlob(message)
        sentiment = blob.sentiment.polarity
        
        # Adjust the tone based on the target personality
        if target_personality == "formal":
            if sentiment < 0:
                message = message.upper()
            else:
                message = message.capitalize()
        elif target_personality == "casual":
            if sentiment < 0:
                message = message.lower()
            else:
                message = message.lower()
        elif target_personality == "excited":
            message = message.upper() + "!"
        elif target_personality == "serious":
            message = message.lower()
        else:
            return json.dumps({"error": "Invalid target personality"})
        
        return json.dumps({"rewritten_message": message})
    except Exception as e:
        return json.dumps({"error": str(e)})