import requests

def run(query: str) -> str:
    """
    Provides comprehensive weather information, focusing on temperature in Celsius and current weather conditions for specified locations.
    """
    api_key = 'your_api_key_here'  # Replace with actual API key
    base_url = "http://api.weatherapi.com/v1/current.json"
    params = {
        'key': api_key,
        'q': query,
        'aqi': 'no'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        location = data['location']['name']
        temp_c = data['current']['temp_c']
        condition = data['current']['condition']['text']
        return f"Location: {location}, Temperature: {temp_c}°C, Condition: {condition}"
    except requests.RequestException as e:
        return f"Error: {e}"