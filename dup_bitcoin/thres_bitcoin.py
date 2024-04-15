import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from pycoingecko import CoinGeckoAPI
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np
from plyer import notification

# Function to fetch historical price data from CoinGecko API with rate limiting
def fetch_historical_data(coin_id, days):
    cg = CoinGeckoAPI()
    historical_data = None

    # Retry mechanism with exponential backoff
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session = requests.Session()
    session.mount('https://api.coingecko.com', HTTPAdapter(max_retries=retries))
    
    try:
        end_timestamp = int(time.time())
        start_timestamp = end_timestamp - (days * 24 * 60 * 60)
        historical_data = cg.get_coin_market_chart_range_by_id(id=coin_id, vs_currency='usd', from_timestamp=start_timestamp, to_timestamp=end_timestamp)
    except requests.exceptions.RequestException as e:
        print(f"HTTP error occurred: {e}")
        time.sleep(60)  # Wait for a minute before retrying
        fetch_historical_data(coin_id, days)  # Retry the request

    if historical_data is None:
        return pd.DataFrame()  # Return empty DataFrame if data retrieval fails

    prices = pd.DataFrame(historical_data['prices'], columns=['timestamp', 'price'])
    prices['timestamp'] = pd.to_datetime(prices['timestamp'], unit='ms')
    return prices

# Function to forecast prices using linear regression
def forecast_prices(coin_id, days):
    # Fetch historical data
    historical_data = fetch_historical_data(coin_id, days)
    
    if historical_data.empty:
        print(f"Failed to retrieve historical data for {coin_id}")
        return None
    
    # Prepare data for regression
    X = historical_data.index.values.reshape(-1, 1)
    y = historical_data['price'].values

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train linear regression model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Make predictions
    forecasted_days = np.arange(len(historical_data), len(historical_data) + days).reshape(-1, 1)
    forecasted_prices = model.predict(forecasted_days)

    return forecasted_prices

# Function to monitor price changes and send notifications
def monitor_price_changes(cryptocurrencies, forecast_days):
    while True:
        for coin_id in cryptocurrencies:
            # Fetch latest price data
            latest_data = fetch_historical_data(coin_id, days=7)
            if not latest_data.empty:
                # Process the data and perform analysis
                print(f"Processed data for {coin_id}:")
                print(latest_data)
                
                # Forecast prices
                forecasted_prices = forecast_prices(coin_id, forecast_days)
                if forecasted_prices is not None:
                    print(f"Forecasted prices for {coin_id}:")
                    print(forecasted_prices)

                    # Get current price and time
                    current_price = latest_data.iloc[-1]['price']
                    current_time = latest_data.iloc[-1]['timestamp']

                    # Find the highest forecasted price
                    highest_forecast = np.max(forecasted_prices)

                    # Format notification message with current price, time, and highest forecasted price
                    notification_message = f"Current Price: ${current_price:.2f} (as of {current_time})\n\nForecasted Price: ${highest_forecast:.2f}"

                    # Send notification
                    notification_title = f"{coin_id.capitalize()} Price Forecast"
                    notification.notify(
                        title=notification_title,
                        message=notification_message,
                        timeout=10
                    )
            else:
                print(f"Failed to retrieve data for {coin_id}")

        # Sleep for a longer duration before checking again
        time.sleep(5)  # Check every 10 minutes

# Example usage:
# Example usage:
cryptocurrencies = ['bitcoin', 'ethereum', 'cardano', 'litecoin', 'ripple', 'bitcoin-cash', 'binancecoin', 'tron', 'eos', 'dogecoin', 'polkadot', 'stellar', 'chainlink']
forecast_days = 7
monitor_price_changes(cryptocurrencies, forecast_days)
