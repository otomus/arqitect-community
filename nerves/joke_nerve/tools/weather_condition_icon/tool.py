import requests

def run(query: str) -> str:
    """
    Fetches weather condition and temperature for a specified location.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?q={query}&appid=YOUR_API_KEY&units=metric"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        weather = data['weather'][0]['description']
        icon = data['weather'][0]['icon']
        return f"Temperature: {temperature}°C, Weather: {weather}, Icon: {icon}"
    else:
        return "Failed to retrieve weather data"