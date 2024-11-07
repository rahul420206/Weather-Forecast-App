import sqlite3
from datetime import datetime, timedelta

DB_NAME = 'weather_data.db'

import requests

API_KEY = '6f2ea8041e662e9c17ba44dba05833d2'
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'http://api.openweathermap.org/data/2.5/forecast'
CITIES = ['Delhi', 'Mumbai', 'Chennai', 'Bangalore', 'Kolkata', 'Hyderabad']


def validate_data(city):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT date, temperature, feels_like
        FROM weather_data
        WHERE city = ?
        ORDER BY date DESC
        LIMIT 10
    ''', (city,))
    
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    connection.close()

validate_data('Delhi')  # Replace with your city name


def fetch_historical_data(city, hours=None, days=None):
    """Fetch historical weather data for a specific city."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if hours:
        cursor.execute('''
            SELECT date, temperature, feels_like FROM weather_data 
            WHERE city = ? AND date >= datetime('now', '-? hours') 
            ORDER BY date ASC
        ''', (city, hours))
    elif days:
        cursor.execute('''
            SELECT date, temperature, feels_like FROM weather_data 
            WHERE city = ? AND date >= datetime('now', '-? days') 
            ORDER BY date ASC
        ''', (city, days))

    historical_data = cursor.fetchall()
    conn.close()
    return historical_data

def backfill_historical_data(city, lat, lon):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    today = datetime.now()
    
    # Fetch data for the past 7 days
    for days_back in range(1, 8):
        date = today - timedelta(days=days_back)
        timestamp = int(date.timestamp())
        
        response = requests.get(f"{BASE_URL}?lat={lat}&lon={lon}&dt={timestamp}&appid={API_KEY}&units=metric")
        data = response.json()
        
        # Check if data is received
        if response.status_code == 200:
            for hourly_data in data.get('hourly', []):
                temp = hourly_data['temp']
                feels_like = hourly_data['feels_like']
                humidity = hourly_data['humidity']
                wind_speed = hourly_data['wind_speed']
                weather_condition = hourly_data['weather'][0]['description']
                date_time = datetime.fromtimestamp(hourly_data['dt']).strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute('''INSERT OR IGNORE INTO weather_data (city, temperature, feels_like, humidity, wind_speed, weather_condition, date) VALUES (?, ?, ?, ?, ?, ?, ?)''', (city, temp, feels_like, humidity, wind_speed, weather_condition, date_time))
                print(f"Inserted data for {date_time}: {temp}°C, feels like {feels_like}°C")  # Debug output
        else:
            print(f"Error fetching data for {days_back} days back: {data}")  # Debug output for API errors
    
    connection.commit()
    connection.close()

def fetch_future_predictions(city, lat, lon):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    
    # Use correct API endpoint
    response = requests.get(
        f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric'
    )
    data = response.json()
    
    # Check response
    if response.status_code == 200:
        for day in data['list']:
            date_time = datetime.fromtimestamp(day['dt']).strftime('%Y-%m-%d %H:%M:%S')
            temp = day['main']['temp']
            feels_like = day['main']['feels_like']
            
            cursor.execute('''
                INSERT OR IGNORE INTO predictions (city, forecast_date, temp_forecast, feels_like, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (city, date_time, temp, feels_like, date_time))
            print(f"Inserted forecast for {date_time}: Temp={temp}°C, Feels like={feels_like}°C")
    else:
        print(f"Error fetching future data: {data}")
    
    connection.commit()
    connection.close()


def print_table_schema():
    conn = sqlite3.connect('weather_data.db')  # Replace with your database name
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(predictions);")
    schema = cursor.fetchall()
    for column in schema:
        print(column)
    conn.close()

# Call the function to print the schema
print_table_schema()

def store_prediction_data(city, forecast_date, temp_forecast):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO predictions (city, forecast_date, temp_forecast) VALUES (?, ?, ?)
    ''', (city, forecast_date, temp_forecast))
    conn.commit()
    conn.close()

def initialize_database():
    """Initialize the database with necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create weather_data table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            temperature REAL NOT NULL,
            feels_like REAL NOT NULL,
            humidity INTEGER NOT NULL,
            wind_speed REAL NOT NULL,
            weather_condition TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')

    # Create or reset predictions table
    cursor.execute('DROP TABLE IF EXISTS predictions')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            forecast_date TEXT NOT NULL,
            temp_forecast REAL NOT NULL,
            feels_like REAL NOT NULL,
            date TEXT NOT NULL,
            UNIQUE(forecast_date, temp_forecast)
        )
    ''')

    # Create daily_summary table if needed (optional)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            date TEXT NOT NULL,
            avg_temp REAL,
            max_temp REAL,
            min_temp REAL,
            dominant_condition TEXT
        )
    ''')

    conn.commit()
    conn.close()

initialize_database()


def store_daily_summary(city, avg_temp, max_temp, min_temp, dominant_condition):
    """Store daily weather summary in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO daily_summary (city, date, avg_temp, max_temp, min_temp, dominant_condition)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (city, datetime.now().date(), avg_temp, max_temp, min_temp, dominant_condition))

    conn.commit()
    conn.close()

def fetch_daily_summary():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM daily_summary ORDER BY date DESC')
    data = cursor.fetchall()
    
    conn.close()
    return data

def store_alert(city, message, temperature):
    """Store alerts in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO alerts (city, message, temperature)
        VALUES (?, ?, ?)
    ''', (city, message, temperature))

    conn.commit()
    conn.close()

def store_weather_data(city, temp, feels_like, humidity, wind_speed, condition):
    """Store current weather data in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO weather_data (city, date, temperature, feels_like, humidity, wind_speed, condition)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (city, datetime.now(), temp, feels_like, humidity, wind_speed, condition))

    conn.commit()
    conn.close()

def fetch_historical_data(city, days=None, hours=None):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    if days:
        days_ago = datetime.now() - timedelta(days=days)
        cursor.execute('''
            SELECT date, temperature, feels_like, humidity, wind_speed
            FROM weather_data
            WHERE city = ? AND date >= ?
            ORDER BY date ASC
        ''', (city, days_ago))
    elif hours:
        hours_ago = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT date, temperature, feels_like, humidity, wind_speed
            FROM weather_data
            WHERE city = ? AND date >= ?
            ORDER BY date ASC
        ''', (city, hours_ago))

    data = cursor.fetchall()
    connection.close()
    return data

def store_prediction_data(city, forecast_date, temp_forecast, feels_like=None):
    """Store the predicted temperature data in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO predictions (city, forecast_date, temp_forecast, feels_like, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (city, forecast_date, temp_forecast, feels_like, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()
    conn.close()
    

def fetch_predictions(city):
    predictions = {}
    response = requests.get(FORECAST_URL, params={'q': city, 'appid': API_KEY, 'units': 'metric'})  # Use the correct API URL for forecasts
    
    print(f"Fetching predictions for {city}: {response.url}")  # Debug line
    
    if response.status_code == 200:
        data = response.json()
        print(f"Prediction data for {city}: {data}")  # Debug line
        
        # Check if 'list' key exists in the response
        if 'list' in data:
            for day in data['list']:
                date = datetime.fromtimestamp(day['dt']).strftime('%Y-%m-%d')
                temp = day['main']['temp']  # Adjust as necessary to get temperature
                feels_like = day['main']['feels_like']  # If you also want feels like
                predictions[date] = {
                    'temp': round(temp, 2),
                    'feels_like': round(feels_like, 2)
                }
        else:
            print(f"No forecast data available for {city}: {data}")
    else:
        print(f"Error fetching predictions for {city}: {response.status_code} - {response.text}")

    return predictions


def print_predictions(city):
    predictions = fetch_predictions(city)
    if predictions:
        print("Predicted Weather:")
        print("Date\tPredicted Temp (°C)\tFeels Like (°C)")
        for forecast_date, temp_forecast, feels_like in predictions:
            print(f"{forecast_date}\t{temp_forecast}\t{feels_like}")
    else:
        print("No predictions found.")

def fetch_weather_data():
    global weather_data
    for city in CITIES:
        url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric"  # Using metric for Celsius
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            main = data['main']
            weather_condition = data['weather'][0]['main']
            temp = main['temp']
            feels_like = main['feels_like']
            dt = data['dt']

            weather_data.append({
                'city': city,
                'temp': temp,
                'feels_like': feels_like,
                'weather_condition': weather_condition,
                'timestamp': dt
            })
        else:
            print(f"Failed to get data for {city}: {response.status_code}")


def check_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Tables in the database:")
    for table in tables:
        print(table[0])

    conn.close()

# Check the tables in the database
check_tables()
