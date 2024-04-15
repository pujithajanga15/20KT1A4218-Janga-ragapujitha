from flask import Flask, render_template
from flask_socketio import SocketIO
import requests
import time

app = Flask(__name__)
socketio = SocketIO(app)

# List of cryptocurrencies
CRYPTOCURRENCIES = ['bitcoin', 'ethereum', 'cardano', 'litecoin', 'ripple', 'bitcoin-cash', 'binancecoin', 'tron', 'eos', 'dogecoin', 'polkadot', 'stellar', 'chainlink']

# Function to fetch cryptocurrency data and provide recommendations
def fetch_cryptocurrency_data():
    while True:
        try:
            ids = ','.join(CRYPTOCURRENCIES)
            response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd')
            if response.status_code == 429:
                print("Rate limit exceeded. Waiting for 1 minute...")
                time.sleep(60)
                continue
            
            data = response.json()

            # Calculate recommendations based on prices
            recommendations = {}
            for currency, price_data in data.items():
                price = price_data.get('usd', 0)
                if price > 5000:
                    recommendations[currency] = 'Sell'
                elif price < 2000:
                    recommendations[currency] = 'Buy'
                else:
                    recommendations[currency] = 'Hold'

            print("Sending data to client:", {'prices': data, 'recommendations': recommendations})
            socketio.emit('update_data', {'prices': data, 'recommendations': recommendations})
            time.sleep(5)  # Fetch data every 5 seconds
        except Exception as e:
            print("Error fetching cryptocurrency data:", e)
            time.sleep(60)  # Retry after 1 minute if there's an error

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.start_background_task(fetch_cryptocurrency_data)
    socketio.run(app, debug=True)
