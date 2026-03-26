import json
from textblob import TextBlob

def personality_rewriter(message: str, target_personality: str) -> str:
    """
    Rewrites messages to match a specified personality tone without translation.
    """
    try:
        # Analyze the current personality of the message
        blob = TextBlob(message)
        current_personality = blob.sentiment.polarity
        
        # Adjust the message based on the target personality
        if target_personality == "positive":
            if current_personality < 0:
                message = blob.correct()
            elif current_personality == 0:
                message = message.upper()
        elif target_personality == "negative":
            if current_personality > 0:
                message = blob.correct()
            elif current_personality == 0:
                message = message.lower()
        elif target_personality == "neutral":
            message = message.capitalize()
        else:
            return json.dumps({"error": "Invalid target personality"})
        
        return json.dumps({"rewritten_message": str(message)})
    except Exception as e:
        return json.dumps({"error": str(e)})