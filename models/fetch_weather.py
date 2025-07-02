from datetime import datetime

# Helper functions for weather data processing
def get_location_name(lat, lon):
    """Get a location name based on coordinates"""
    # Normally this would use a reverse geocoding API
    # This is a simplified version that returns a placeholder
    try:
        import requests
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {'User-Agent': 'GreenSathi/1.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            
            # Try to get village, city, or state name
            location = address.get('village') or address.get('town') or address.get('city') or address.get('state')
            
            if location:
                return location
    except Exception as e:
        print(f"Error getting location name: {str(e)}")
    
    return "Your Farm Location"

def get_weather_condition(code):
    """Convert WMO weather code to human-readable condition"""
    conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return conditions.get(code, "Unknown")

def get_weather_icon(code):
    """Get a weather icon URL based on the WMO weather code"""
    # Map codes to icon names (using Font Awesome for simplicity)
    if code == 0:
        return "https://cdn.weatherapi.com/weather/64x64/day/113.png"  # Clear
    elif code in [1, 2]:
        return "https://cdn.weatherapi.com/weather/64x64/day/116.png"  # Partly cloudy
    elif code == 3:
        return "https://cdn.weatherapi.com/weather/64x64/day/119.png"  # Cloudy
    elif code in [45, 48]:
        return "https://cdn.weatherapi.com/weather/64x64/day/143.png"  # Mist
    elif code in [51, 53, 55, 56, 57]:
        return "https://cdn.weatherapi.com/weather/64x64/day/263.png"  # Drizzle
    elif code in [61, 63, 65, 66, 67, 80, 81, 82]:
        return "https://cdn.weatherapi.com/weather/64x64/day/308.png"  # Rain
    elif code in [71, 73, 75, 77, 85, 86]:
        return "https://cdn.weatherapi.com/weather/64x64/day/338.png"  # Snow
    elif code in [95, 96, 99]:
        return "https://cdn.weatherapi.com/weather/64x64/day/389.png"  # Thunderstorm
    else:
        return "https://cdn.weatherapi.com/weather/64x64/day/116.png"  # Default to partly cloudy

def get_current_humidity(hourly_data):
    """Get the current relative humidity from hourly data"""
    if hourly_data and 'relativehumidity_2m' in hourly_data and hourly_data['relativehumidity_2m']:
        # Return the first value as current
        return hourly_data['relativehumidity_2m'][0]
    return 70  # Default value

def get_current_precipitation(hourly_data):
    """Get the current precipitation from hourly data"""
    if hourly_data and 'precipitation' in hourly_data and hourly_data['precipitation']:
        # Return the first value as current
        return hourly_data['precipitation'][0]
    return 0  # Default value

def get_hourly_weather_codes(hourly_data, full_data):
    """Generate weather codes for hourly data"""
    # This is a simplification as the hourly data might not include weather codes
    # We'll use the daily weather code for all hours of that day
    if 'daily' in full_data and 'weathercode' in full_data['daily']:
        daily_codes = full_data['daily']['weathercode']
        hours_per_day = 24
        
        result = []
        for i in range(len(hourly_data.get('time', []))):
            day_index = i // hours_per_day
            if day_index < len(daily_codes):
                result.append(daily_codes[day_index])
            else:
                result.append(0)  # Default clear sky
        return result
    
    return [0] * len(hourly_data.get('time', []))  # Default all to clear sky

def format_time(time_str):
    """Format ISO time string to HH:MM format"""
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M')
    except:
        return time_str

def generate_farming_advice(current, precipitation, soil):
    """Generate farming advice based on weather conditions"""
    advice = []
    
    # Temperature-based advice
    temp = current.get('temperature', 0)
    if temp > 35:
        advice.append("High temperature alert: Ensure crops have adequate water. Consider adding shade for sensitive plants.")
    elif temp > 30:
        advice.append("Warm conditions: Water crops in the evening to reduce evaporation.")
    elif temp < 10:
        advice.append("Cold conditions: Protect sensitive crops from frost. Delay seeding cold-sensitive crops.")
    
    # Rain-based advice
    today_rain = precipitation.get('today', 0)
    tomorrow_rain = precipitation.get('tomorrow', 0)
    
    if today_rain > 10:
        advice.append("Heavy rain today: Ensure proper drainage in fields. Postpone fertilizer application.")
    elif today_rain > 5:
        advice.append("Moderate rain today: Good conditions for transplanting. No irrigation needed.")
    elif today_rain < 2 and tomorrow_rain < 2:
        advice.append("Dry conditions: Consider irrigation for water-sensitive crops.")
    
    if tomorrow_rain > 10:
        advice.append("Heavy rain expected tomorrow: Delay any planned pesticide or fertilizer application.")
    
    # Wind-based advice
    wind_speed = current.get('wind_speed', 0)
    if wind_speed > 25:
        advice.append("Strong winds: Avoid spraying operations. Check supports for tall crops.")
    elif wind_speed > 15:
        advice.append("Moderate winds: Exercise caution with spraying operations.")
    
    # Soil-based advice
    soil_moisture = soil.get('moisture_percent', 0)
    if soil_moisture < 30:
        advice.append("Low soil moisture: Prioritize irrigation, especially for shallow-rooted crops.")
    elif soil_moisture > 70:
        advice.append("High soil moisture: Be cautious of root diseases. Ensure proper drainage.")
    
    # If no specific advice, add general advice
    if not advice:
        advice.append("Good farming conditions today. Continue regular agricultural activities.")
    
    return advice