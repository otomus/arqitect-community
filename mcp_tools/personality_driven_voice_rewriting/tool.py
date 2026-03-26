import json
from textblob import TextBlob

def personality_driven_voice_rewriting(message: str, personality_tone: str) -> str:
    """
    Rewrites messages to match a specified personality tone without translation.
    """
    try:
        blob = TextBlob(message)
        if personality_tone == "formal":
            return json.dumps(blob.string.replace("I", "We").replace("my", "our"))
        elif personality_tone == "casual":
            return json.dumps(blob.string.replace("We", "I").replace("our", "my"))
        else:
            return json.dumps("Error: Unsupported personality tone")
    except Exception as e:
        return json.dumps(f"Error: {str(e)}")