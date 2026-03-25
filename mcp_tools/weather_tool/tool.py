import requests
import json

def weather_tool(query: str) -> str:
    """
    Fetches the current weather for a given location using its name.
    
    Parameters:
    query (str): The name of the location.
    
    Returns:
    str: A JSON string containing the current weather information.
    """
    try:
        # Step 1: Geocode the location
        geo = requests.get(f'https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1').json()
        lat = geo['results'][0]['latitude']
        lon = geo['results'][0]['longitude']
        
        # Step 2: Fetch the weather forecast
        weather = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true').json()
        temp = weather['current_weather']['temperature']
        wind = weather['current_weather']['windspeed']
        
        # Prepare the result
        result = {
            'location': query,
            'temperature': temp,
            'windspeed': wind
        }
        
        return json.dumps(result)
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    except KeyError as e:
        return f"Error: Missing key in response - {e}"