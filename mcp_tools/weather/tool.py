"""Get current weather or a forecast for a location."""

import json
import os

try:
    import requests
except ImportError:
    requests = None

BASE_URL = "https://api.weatherapi.com/v1"


def run(location: str, operation: str, days: str = "") -> str:
    """Fetch current weather or a multi-day forecast.

    @param location: City name or coordinates.
    @param operation: 'current' for now, 'forecast' for multi-day.
    @param days: Number of forecast days (defaults to 3).
    @returns JSON string with weather data.
    @throws ValueError: If the operation is invalid or API key is missing.
    """
    if operation == "current":
        return _current(location)
    if operation == "forecast":
        return _forecast(location, days)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'current' or 'forecast'.")


def _get_api_key() -> str:
    """Retrieve the weather API key from environment."""
    key = os.environ.get("WEATHER_API_KEY", "")
    if not key:
        raise ValueError("WEATHER_API_KEY environment variable is required")
    return key


def _current(location: str) -> str:
    """Get current weather conditions."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    api_key = _get_api_key()
    url = f"{BASE_URL}/current.json"
    response = requests.get(url, params={"key": api_key, "q": location}, timeout=10)
    response.raise_for_status()
    data = response.json()

    current = data.get("current", {})
    return json.dumps({
        "location": data.get("location", {}).get("name", location),
        "temperature_c": current.get("temp_c"),
        "temperature_f": current.get("temp_f"),
        "condition": current.get("condition", {}).get("text", ""),
        "humidity": current.get("humidity"),
        "wind_kph": current.get("wind_kph"),
    }, indent=2)


def _forecast(location: str, days: str) -> str:
    """Get a multi-day weather forecast."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    api_key = _get_api_key()
    num_days = int(days) if days else 3
    url = f"{BASE_URL}/forecast.json"
    response = requests.get(
        url, params={"key": api_key, "q": location, "days": num_days}, timeout=10
    )
    response.raise_for_status()
    data = response.json()

    forecast_days = []
    for day in data.get("forecast", {}).get("forecastday", []):
        forecast_days.append({
            "date": day.get("date"),
            "max_temp_c": day.get("day", {}).get("maxtemp_c"),
            "min_temp_c": day.get("day", {}).get("mintemp_c"),
            "condition": day.get("day", {}).get("condition", {}).get("text", ""),
        })

    return json.dumps({
        "location": data.get("location", {}).get("name", location),
        "days": num_days,
        "forecast": forecast_days,
    }, indent=2)
