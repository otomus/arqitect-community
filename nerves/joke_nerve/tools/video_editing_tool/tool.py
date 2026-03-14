import requests

def run(query: str) -> str:
    """
    Generates an animated GIF from a text description using external tools.
    
    Args:
    query (str): The text description of the animation.
    
    Returns:
    str: A URL to the generated animated GIF.
    
    Raises:
    requests.exceptions.RequestException: If there was an error with the request.
    """
    url = "https://api.example.com/generate_gif"
    payload = {'text': query}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['gif_url']
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"