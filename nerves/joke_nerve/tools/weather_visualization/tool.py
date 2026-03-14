import requests

def run(query: str) -> str:
    """
    Tool for providing detailed weather information, including temperature in Celsius and current weather conditions, for any specified location.
    """
    url = f"http://api.weatherapi.com/v1/current.json?key=YOUR_API_KEY&q={query}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        temp_c = data['current']['temp_c']
        condition = data['current']['condition']['text']
        return f"Current temperature in {query} is {temp_c}°C and the weather condition is {condition}."
    except requests.RequestException as e:
        return f"Error fetching weather data: {e}"