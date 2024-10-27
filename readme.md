# Weather Visualization App

This Weather Visualization App is a Flask-based web application that provides visualizations and historical statistics for temperatures in various cities. The app displays temperature trends for the past 24 hours or last 7 days, using real-time data and backfilling where necessary.

## Features

- Select a city to view its temperature trends.
- Choose between a 24-hour or 7-day view for weather data visualization.
- Displays historical temperature statistics, including average and maximum temperatures.
- Automatically backfills data if historical data is missing.
- Provides clear visualizations of temperature and 'feels like' trends.

## Setup

### Prerequisites

- Python 3.6 or later
- Flask and other required libraries listed in `requirements.txt`

### Installation

1.  **Clone the repository**:

    ```bash
    git clone <repository_url>
    cd weather-visualization-app

    ```

2.  **Get an API key**:
    you can get a free API key from here and paste it in the main.py file
    Weather App API key website: https://home.openweathermap.org/api_keys

3.  **Install the requirements**:
    Paste and run this commanf in the terminal: pip install -r requirements.txt

4.  **Run the App**:
    open a new terminal
    and run this command:

        python main.py
