from flask import Flask, render_template, request, jsonify, redirect, url_for
import time, base64, requests, threading
from io import BytesIO
from datetime import datetime
from weather_database import store_prediction_data, fetch_predictions, backfill_historical_data, fetch_future_predictions, fetch_weather_data
from weather_database import (
    initialize_database,
    store_weather_data,
    fetch_historical_data,
    store_daily_summary,
    store_alert
)
import matplotlib.pyplot as plt

import sqlite3

DB_NAME = 'weather_data.db'

app = Flask(__name__)

initialize_database()

# OpenWeatherMap API settings
API_KEY = 'go_to_readme_file'
UPDATE_INTERVAL = 300
CITIES = ['Delhi', 'Mumbai', 'Chennai', 'Bangalore', 'Kolkata', 'Hyderabad']
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'http://api.openweathermap.org/data/2.5/forecast'
user_threshold_temp = 25  # Set your threshold here
prediction_data = {}  # Dictionary to store unique predictions 
weather_data = {}
daily_summary = {}

city_coordinates = {
    'Delhi': {'lat': 28.6139, 'lon': 77.2090},
    'Mumbai': {'lat': 19.0760, 'lon': 72.8777},
    'Bangalore': {'lat': 12.9716, 'lon': 77.5946},
    'Hyderabad': {'lat': 17.4065, 'lon': 78.4772},
    'Chennai': {'lat': 13.0843, 'lon': 80.2705},
    'Kolkata': {'lat': 22.5744, 'lon': 88.3629}

}

def store_weather_data(city, temp, feels_like, humidity, wind_speed, weather_main):
    """Store current weather data in the database or any storage."""
    print(f"Storing data for {city} - Temp: {temp}°C, Feels like: {feels_like}°C, Humidity: {humidity}%, Wind: {wind_speed} m/s, Weather: {weather_main}")

def store_prediction_data(city, forecast_date, temp_forecast):
    """Store forecasted weather data in the database or any storage."""
    print(f"Storing forecast for {city} - Date: {forecast_date}, Temp: {temp_forecast}°C")

@app.route("/", methods=["GET"])
def home():
    selected_city = request.args.get('city', 'Delhi')
    threshold_temp = request.args.get('threshold', type=float)  # Use this to get user-defined threshold
    
    weather_data, alert_message = fetch_weather(selected_city)
    predictions = fetch_predictions(selected_city)
    
    # Get historical stats for display
    historical_stats = fetch_historical_stats(selected_city)
    
    return render_template(
        'weather_app.html',
        cities=CITIES,
        selected_city=selected_city,
        weather_data=weather_data,
        predictions=predictions,
        alert_message=alert_message,
        threshold_temp=threshold_temp,
        historical_stats=historical_stats
    )


@app.route("/", methods=["GET"])
def weather_dashboard():
    city = request.args.get("city", default="Hyderabad")
    weather_data, alert_message = fetch_weather(city)  # Fetch both weather data and alert message

    # Fetch predictions from the database
    predictions = fetch_predictions(city)
    
    return render_template(
        "weather_app.html",
        weather_data=weather_data,
        selected_city=city,
        predictions=predictions,
        alert_message=alert_message  # Pass alert message to the template
    )

def fetch_current_weather(city):
    """Fetch current weather data for a given city with minimal data retrieval."""
    try:
        # Build the URL with the city and API key
        url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric"  # Use 'metric' for Celsius
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            if 'main' in data:  # Check if the 'main' section exists
                current_temp = data['main']['temp']  # Get the current temperature
                return {'temperature': current_temp}
            else:
                print(f"No weather data available for {city}.")
                return None
        else:
            print(f"Error fetching weather data: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
    
def fetch_weather_periodically():
    """Fetch weather data periodically every UPDATE_INTERVAL seconds."""
    while True:
        for city in CITIES:
            fetch_weather(city)
        time.sleep(UPDATE_INTERVAL)

def fetch_weather(city):
    alert_message = None  # Initialize alert_message as None
    response = requests.get(BASE_URL, params={'q': city, 'appid': API_KEY, 'units': 'metric'})
    
    print(f"Response for {city}: {response.json()}")  # Log the API response for debugging

    if response.status_code == 200:
        data = response.json()
        if 'main' in data:
            main = data['main']
            wind = data['wind']
            weather = data['weather'][0]
            temp_celsius = main['temp']
            feels_like_celsius = main['feels_like']
            humidity = main['humidity']
            wind_speed = wind['speed']
            weather_data[city] = {
                'city': city,
                'main': weather['main'],
                'temp': round(temp_celsius, 2),
                'feels_like': round(feels_like_celsius, 2),
                'condition': weather['description'], 
                'humidity': humidity,
                'wind_speed': wind_speed,
                'dt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            store_weather_data(city, temp_celsius, feels_like_celsius, humidity, wind_speed, weather['main'])  # Ensure this function is defined
            # Check if the current temperature exceeds the threshold
            if temp_celsius >= user_threshold_temp:
                alert_message = f"ALERT: {city} temperature is {temp_celsius:.2f}°C, which exceeds the threshold of {user_threshold_temp}°C."
            else:
                print(f"{city}: Current temperature is {temp_celsius:.2f}°C - within threshold.")
        else:
            print(f"No 'main' key in response for {city}: {data}")
    else:
        print(f"Error fetching data for {city}: {response.status_code} - {response.text}")
    
    # Return weather data for the selected city and the alert message
    return weather_data.get(city, {}), alert_message  # Make sure the weather_data is returned correctly

def fetch_historical_stats(city):
    # Get historical data (assuming this function already fetches the data you need for the graph)
    historical_data = fetch_historical_data(city)
    
    if not historical_data:
        return {"average_temp": None, "max_temp": None, "min_temp": None, "dominant_condition": None}
    
    temperatures = [entry['temp'] for entry in historical_data]
    conditions = [entry['condition'] for entry in historical_data]
    max_temp = max(entry['temp_max'] for entry in historical_data)  # Using 'temp_max' from your data
    min_temp = min(entry['temp_min'] for entry in historical_data)  # Using 'temp_min' from your data
    avg_temp = sum(temperatures) / len(temperatures)  # Calculate the average temperature
    
    # Calculate the dominant weather condition
    condition_counts = {}
    for condition in conditions:
        if condition in condition_counts:
            condition_counts[condition] += 1
        else:
            condition_counts[condition] = 1
    dominant_condition = max(condition_counts, key=condition_counts.get)
    
    # Return stats to be displayed
    return {
        "average_temp": round(avg_temp, 2),
        "max_temp": max_temp,
        "min_temp": min_temp,
        "dominant_condition": dominant_condition
    }


def update_daily_summary(city, temp, condition, dt):
    """Update the daily summary for the weather data."""
    date = dt.date()
    if date not in daily_summary:
        daily_summary[date] = {
            'city': city,
            'max_temp': temp,
            'min_temp': temp,
            'total_temp': temp,
            'count': 1,
            'conditions': [condition]
        }
    else:
        daily_summary[date]['max_temp'] = max(daily_summary[date]['max_temp'], temp)
        daily_summary[date]['min_temp'] = min(daily_summary[date]['min_temp'], temp)
        daily_summary[date]['total_temp'] += temp
        daily_summary[date]['count'] += 1
        daily_summary[date]['conditions'].append(condition)

    # Calculate daily average and dominant condition
    avg_temp = daily_summary[date]['total_temp'] / daily_summary[date]['count']
    dominant_condition = max(set(daily_summary[date]['conditions']), key=daily_summary[date]['conditions'].count)

    # Store summary in database at end of the day
    if datetime.now().hour == 23 and datetime.now().minute == 59:
        store_daily_summary(
            city,
            round(avg_temp, 2),
            daily_summary[date]['max_temp'],
            daily_summary[date]['min_temp'],
            dominant_condition
        )
def check_alerts(city):
    """Check current temperature and alert if it exceeds the user-defined threshold."""
    global user_threshold
    while True:
        current_weather = fetch_current_weather(city)  # Fetch current weather data for the city
        if current_weather and user_threshold is not None:
            current_temp = current_weather['temperature']
            if current_temp > user_threshold:
                print(f"Alert: The current temperature in {city} is {current_temp}°C, exceeding your set threshold of {user_threshold}°C.")
                # Here, you can also call store_alert if you want to store the alert in the database
        time.sleep(300)  # Check every 5 minutes

# Start the alert checking thread for the specified city
threading.Thread(target=check_alerts, args=('YourCityName',), daemon=True).start()

@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    global user_threshold
    data = request.get_json()
    user_threshold = float(data['threshold'])
    return jsonify(success=True)

@app.route('/visualization')
def visualize_weather():
    selected_city = request.args.get('city', 'Delhi')
    view = request.args.get('view', '7days')

    # Fetch historical statistics
    historical_stats = fetch_historical_stats(selected_city)
    print("Fetched Historical Stats before backfill:", historical_stats)

    # Get latitude and longitude for the selected city
    city_info = city_coordinates.get(selected_city, None)
    if city_info:
        lat, lon = city_info['lat'], city_info['lon']
    else:
        return f"Coordinates for {selected_city} not found.", 400

    # Fetch historical data based on the view parameter
    if view == '24hours':
        historical_data = fetch_historical_data(selected_city, hours=24)
        title_suffix = 'Last 24 Hours'
    else:
        historical_data = fetch_historical_data(selected_city, days=7)
        title_suffix = 'Last 7 Days'

    # Backfill data if historical statistics are missing
    if historical_stats is None:
        # Perform backfill if needed
        backfill_historical_data(selected_city, lat, lon)
        historical_stats = fetch_historical_stats(selected_city)
        print("Fetched Historical Stats after backfill:", historical_stats)

        # Use mock data if still empty
        if historical_stats is None:
            historical_stats = {
                'average_temp': 25.5,
                'max_temp': 32.0
            }

    # Prepare data for visualization
    if historical_data:
        dates = [item[0] for item in historical_data]
        temps = [item[1] for item in historical_data]
        feels_likes = [item[2] for item in historical_data]
    else:
        dates, temps, feels_likes = [], [], []
    
    # Plot the historical trends if data is available
    fig, ax = plt.subplots()
    if dates and temps:
        ax.plot(dates, temps, label='Temperature')
        ax.plot(dates, feels_likes, label='Feels Like')
    ax.set_title(f'Temperature Trends for {selected_city} ({title_suffix})')
    ax.set_xlabel('Date')
    ax.set_ylabel('Temperature (°C)')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot to display in the template
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    # Pass historical_stats to the template
    return render_template('visualization.html', city=selected_city, historical_stats=historical_stats, plot_url=plot_url)

@app.route("/visualization")
def visualization():
    selected_city = request.args.get('city', 'Delhi')
    
    # Calculate the historical stats for the selected city
    historical_stats = fetch_historical_stats(selected_city)
    
    return render_template(
        'visualization.html',
        selected_city=selected_city,
        historical_stats=historical_stats
    )


if __name__ == '__main__':
    # Start the background task to fetch weather data periodically
    threading.Thread(target=fetch_weather_periodically, daemon=True).start()
    app.run(debug=True)