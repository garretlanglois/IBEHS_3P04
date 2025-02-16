from flask import Flask, render_template
from flask_socketio import SocketIO
import random
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

def fake_data_emitter():
    """Emit fake data every second to simulate ESP8266 sensor data."""
    while True:
        # Simulate sensor/Arduino data
        data = {'value': random.randint(0, 100)}
        socketio.emit('data', data)
        socketio.sleep(1)  # Use socketio.sleep instead of time.sleep

if __name__ == '__main__':
    # Start the fake data emitter thread
    thread = threading.Thread(target=fake_data_emitter)
    thread.daemon = True
    thread.start()
    # Run the Flask app with WebSocket support
    socketio.run(app, debug=True)
