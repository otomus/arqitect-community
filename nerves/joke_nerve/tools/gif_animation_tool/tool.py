import requests

def run(query: str) -> str:
    """
    Generates an animated GIF from a text description using an external service.
    
    Parameters:
    - query: str - A text description of the animation to generate.
    
    Returns:
    - str: A URL to the generated animated GIF.
    """
    try:
        response = requests.post('https://api.gif-animation-service.com/generate', json={'query': query})
        response.raise_for_status()
        return response.json()['gif_url']
    except requests.exceptions.RequestException as e:
        return f"Error generating GIF: {e}"