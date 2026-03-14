import requests

def run(query: str) -> str:
    """
    Fetch and return detailed weather information for a specified location.
    """
    api_key = 'YOUR_API_KEY'  # Replace with actual API key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}appid={api_key}&q={query}"
    
    try:
        response = requests.get(complete_url)
        weather_data = response.json()
        
        if weather_data['cod'] == 200:
            main_data = weather_data['main']
            temperature = main_data['temp'] - 273.15  # Convert Kelvin to Celsius
            weather_condition = weather_data['weather'][0]['description']
            return f"Temperature: {temperature:.2f}°C, Condition: {weather_condition}"
        else:
            return "City not found or API request failed."
    except requests.RequestException as e:
        return f"Error: {e}"