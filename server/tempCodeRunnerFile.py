import asyncio
import websockets
import struct
import numpy as np
from collections import deque
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import threading
import queue

# Increased buffer size to capture longer periods (3 seconds worth of data)
x_values = deque(maxlen=300)
y_values = deque(maxlen=300)
z_values = deque(maxlen=300)
magnitude_values = deque(maxlen=300)
message_count = 0
fft_data_queue = queue.Queue()

# Initialize FFT data
freq_data = np.zeros(150)  # Increased to accommodate more frequency points
x_fft_data = np.zeros(150)
y_fft_data = np.zeros(150)
z_fft_data = np.zeros(150)
magnitude_fft_data = np.zeros(150)

# Define sampling rate (samples per second)
SAMPLING_RATE = 100  # 10ms = 0.01s per sample = 100 Hz

# Create Dash application
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Real-time FFT Display"),
    dcc.Graph(id='x-fft-graph'),
    dcc.Graph(id='y-fft-graph'),
    dcc.Graph(id='z-fft-graph'),
    dcc.Graph(id='magnitude-fft-graph'),
    dcc.Interval(
        id='interval-component',
        interval=500,  # in milliseconds
        n_intervals=0
    ),
])

@app.callback(
    [Output('x-fft-graph', 'figure'),
     Output('y-fft-graph', 'figure'),
     Output('z-fft-graph', 'figure'),
     Output('magnitude-fft-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    # Check if there's new FFT data to display
    if not fft_data_queue.empty():
        global freq_data, x_fft_data, y_fft_data, z_fft_data, magnitude_fft_data
        freq_data, x_fft_data, y_fft_data, z_fft_data, magnitude_fft_data = fft_data_queue.get()
    
    # Common layout settings for all graphs
    axis_layout = {
        'xaxis': {
            'title': 'Frequency (Hz)',
            'range': [0, 5]  # Reduced to focus better on lower frequencies (like 0.67 Hz)
        },
        'yaxis': {
            'title': 'Magnitude'
        }
    }
    
    # Create figures
    x_fig = {
        'data': [go.Scatter(x=freq_data, y=x_fft_data, mode='lines')],
        'layout': {
            'title': 'FFT of X-axis (Bandpass 0.5-10 Hz)',
            **axis_layout
        }
    }
    
    y_fig = {
        'data': [go.Scatter(x=freq_data, y=y_fft_data, mode='lines')],
        'layout': {
            'title': 'FFT of Y-axis (Bandpass 0.5-10 Hz)',
            **axis_layout
        }
    }
    
    z_fig = {
        'data': [go.Scatter(x=freq_data, y=z_fft_data, mode='lines')],
        'layout': {
            'title': 'FFT of Z-axis (Bandpass 0.5-10 Hz)',
            **axis_layout
        }
    }
    
    magnitude_fig = {
        'data': [go.Scatter(x=freq_data, y=magnitude_fft_data, mode='lines')],
        'layout': {
            'title': 'FFT of Magnitude (sqrt(x²+y²+z²)) (Bandpass 0.5-10 Hz)',
            **axis_layout
        }
    }
    
    return x_fig, y_fig, z_fig, magnitude_fig

def perform_fft():
    global x_values, y_values, z_values, magnitude_values
    
    x_array = np.array(x_values)
    y_array = np.array(y_values)
    z_array = np.array(z_values)
    magnitude_array = np.array(magnitude_values)
    
    if len(x_array) < 20:  # Need at least some points for meaningful FFT
        return
    
    # Apply window function to reduce spectral leakage
    window = np.hanning(len(x_array))
    x_windowed = x_array * window
    y_windowed = y_array * window
    z_windowed = z_array * window
    magnitude_windowed = magnitude_array * window
        
    x_fft = np.fft.fft(x_windowed)
    y_fft = np.fft.fft(y_windowed)
    z_fft = np.fft.fft(z_windowed)
    magnitude_fft = np.fft.fft(magnitude_windowed)
    
    sample_count = len(x_array)
    
    # Calculate frequencies in Hz based on the sampling rate
    freq = np.fft.fftfreq(sample_count, d=1/SAMPLING_RATE)
    
    # Only keep the positive frequency components (up to Nyquist frequency)
    positive_freq_indices = np.where(freq >= 0)[0]
    freq = freq[positive_freq_indices]
    
    # Get magnitudes and keep only positive frequencies
    x_fft_magnitude = np.abs(x_fft)[positive_freq_indices]
    y_fft_magnitude = np.abs(y_fft)[positive_freq_indices]
    z_fft_magnitude = np.abs(z_fft)[positive_freq_indices]
    magnitude_fft_magnitude = np.abs(magnitude_fft)[positive_freq_indices]
    
    # Scale FFT values by the length of the window
    x_fft_magnitude = x_fft_magnitude / sample_count
    y_fft_magnitude = y_fft_magnitude / sample_count
    z_fft_magnitude = z_fft_magnitude / sample_count
    magnitude_fft_magnitude = magnitude_fft_magnitude / sample_count
    
    # Bandpass filter: 0.5-10 Hz (lowered to include 0.67 Hz)
    # Create frequency mask (true for frequencies we want to keep)
    bandpass_mask = (freq >= 0.5) & (freq <= 10.0)
    
    # Create filtered copies of the FFT data
    x_fft_filtered = np.zeros_like(x_fft_magnitude)
    y_fft_filtered = np.zeros_like(y_fft_magnitude)
    z_fft_filtered = np.zeros_like(z_fft_magnitude)
    magnitude_fft_filtered = np.zeros_like(magnitude_fft_magnitude)
    
    # Only keep values within the bandpass range
    x_fft_filtered[bandpass_mask] = x_fft_magnitude[bandpass_mask]
    y_fft_filtered[bandpass_mask] = y_fft_magnitude[bandpass_mask]
    z_fft_filtered[bandpass_mask] = z_fft_magnitude[bandpass_mask]
    magnitude_fft_filtered[bandpass_mask] = magnitude_fft_magnitude[bandpass_mask]
    
    # Find dominant frequency in the expected range (around 0.67 Hz)
    expected_range = (freq >= 0.5) & (freq <= 1.0)
    if np.any(expected_range):
        mag_in_range = magnitude_fft_filtered[expected_range]
        if len(mag_in_range) > 0:
            peak_idx = np.argmax(mag_in_range) + np.where(expected_range)[0][0]
            peak_freq = freq[peak_idx]
            print(f"Dominant frequency in 0.5-1.0 Hz range: {peak_freq:.3f} Hz")
    
    # Queue the filtered FFT data for the Dash app to pick up
    fft_data_queue.put((freq, x_fft_filtered, y_fft_filtered, z_fft_filtered, magnitude_fft_filtered))
    print("FFT calculated with bandpass (0.5-10 Hz) filter applied")

# WebSocket handler
async def echo(websocket):
    global message_count, x_values, y_values, z_values, magnitude_values

    client_address = websocket.remote_address
    print(f"Client connected: {client_address}")

    try:
        async for message in websocket:
            if len(message) == 12:
                x, y, z = struct.unpack('<fff', message)
                print(f"x: {x}, y: {y}, z: {z}")
                
                # Remove gravity component with a simple high-pass filter
                # (This is a very simple approach - a proper high-pass filter would be better)
                if len(x_values) > 0:
                    alpha = 0.8  # Filter coefficient
                    x = x - (x_values[-1] * alpha)
                    y = y - (y_values[-1] * alpha)
                    z = z - (z_values[-1] * alpha)
                
                x_values.append(x)
                y_values.append(y)
                z_values.append(z)
                
                # Calculate magnitude (sqrt of sum of squares)
                magnitude = np.sqrt(x**2 + y**2 + z**2)
                magnitude_values.append(magnitude)
                
                message_count += 1

                # Perform FFT every 100 samples (1 second)
                if message_count % 100 == 0:
                    perform_fft()
    except websockets.exceptions.ConnectionClosed:
        print(f"Connection closed for {client_address}")

# Start Dash server in a separate thread
def run_dash_server():
    app.run(debug=False, port=8050)

# Main function
async def websocket_server():
    async with websockets.serve(echo, "0.0.0.0", 8000):
        print("WebSocket server started on ws://0.0.0.0:8000")
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour and repeat

def main():
    # Start Dash server in a separate thread
    dash_thread = threading.Thread(target=run_dash_server)
    dash_thread.daemon = True
    dash_thread.start()
    
    # Run the WebSocket server in the main thread
    asyncio.run(websocket_server())

if __name__ == "__main__":
    main()
