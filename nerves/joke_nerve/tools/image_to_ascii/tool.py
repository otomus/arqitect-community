import requests

def run(query: str) -> str:
    """
    Converts an image to ASCII art.
    
    Parameters:
    - query: The URL of the image to convert.
    
    Returns:
    - A string containing the ASCII art.
    """
    try:
        response = requests.get(query)
        response.raise_for_status()
        # Assuming ASCII art service is available at asciiartapi.com
        ascii_art_url = "https://asciiartapi.com/api"
        ascii_response = requests.post(ascii_art_url, data={"image": response.content})
        ascii_response.raise_for_status()
        return ascii_response.text
    except requests.RequestException as e:
        return f"Error: {e}"