import pandas as pd
from datetime import datetime

weather_data = []
daily_summary = {}

def summarize_weather():
    global daily_summary, weather_data
    today = datetime.now().date()
    
    # Create a DataFrame from the weather data
    daily_data = pd.DataFrame(weather_data)

    if not daily_data.empty:
        # Convert timestamp to date
        daily_data['date'] = daily_data['timestamp'].apply(lambda x: datetime.fromtimestamp(x).date())
        
        # Group by date and calculate aggregates
        daily_aggregate = daily_data.groupby('date').agg(
            avg_temp=('temp', 'mean'),
            max_temp=('temp', 'max'),
            min_temp=('temp', 'min'),
            dominant_condition=('weather_condition', lambda x: x.mode()[0])
        ).reset_index()

        # Store the summary
        daily_summary[today] = daily_aggregate
        # Optional: Store daily_summary in a file/database
        print(daily_summary[today])  # Display daily summary for verification

    # Clear data for the next day
    weather_data.clear()
