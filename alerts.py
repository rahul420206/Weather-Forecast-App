weather_data = []
alert_threshold = 15  # Example threshold in Celsius
alert_triggered = False

def check_alerts():
    global alert_triggered
    latest_data = weather_data[-1] if weather_data else None
    if latest_data:
        if latest_data['temp'] > alert_threshold:
            if not alert_triggered:
                print(f"Alert! Temperature exceeded {alert_threshold}°C in {latest_data['city']}.")
                # Here you can add code to send an email or any other notification
                alert_triggered = True
        else:
            alert_triggered = False
