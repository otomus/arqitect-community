import requests

def run(query: str) -> str:
    """
    Fetches weather forecast for a specified location.
    
    Args:
        query (str): The location for which to fetch the weather forecast.
    
    Returns:
        str: A string containing the weather forecast details.
    """
    url = f"http://api.weatherapi.com/v1/current.json?key=YOUR_API_KEY&q={query}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        location = data['location']['name']
        temperature_c = data['current']['temp_c']
        condition = data['current']['condition']['text']
        return f"Weather in {location}: {temperature_c}°C, {condition}"
    except requests.RequestException as e:
        return f"Error fetching weather data: {e}"