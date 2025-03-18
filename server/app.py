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
import time
import csv
import os
from datetime import datetime

x_values = deque(maxlen=1000)
y_values = deque(maxlen=1000)
z_values = deque(maxlen=1000)
magnitude_values = deque(maxlen=1000)

timestamps = deque(maxlen=1000)
message_count = 0
fft_data_queue = queue.Queue()

freq_data = np.zeros(512)
x_fft_data = np.zeros(512)
y_fft_data = np.zeros(512)
z_fft_data = np.zeros(512)
magnitude_fft_data = np.zeros(512)


SAMPLING_RATE = 100.0 


def save_to_csv(y_values, sample_count):
    os.makedirs('data_exports', exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data_exports/y_values_sample_{sample_count}_{timestamp}.csv"
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['sample_index', 'y_value'])
        for i, value in enumerate(y_values):
            writer.writerow([i, value])
    
    print(f"Saved y-values to {filename}")

app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Real-time FFT Display"),
    html.Div(id='sampling-rate-display', style={'fontSize': 18, 'marginBottom': 20}),
    dcc.Graph(id='time-domain-graph'),
    dcc.Graph(id='x-fft-graph'),
    dcc.Graph(id='y-fft-graph'),
    dcc.Graph(id='z-fft-graph'),
    dcc.Graph(id='magnitude-fft-graph'),
    dcc.Interval(
        id='interval-component',
        interval=500, 
        n_intervals=0
    ),
])

@app.callback(
    Output('sampling-rate-display', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_sampling_rate_display(n):
    return f"Measured Sampling Rate: {SAMPLING_RATE:.2f} Hz"

@app.callback(
    Output('time-domain-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_time_domain(n):

    if len(timestamps) > 1:

        start_time = timestamps[0]
        time_array = [(t - start_time) for t in timestamps]
    else:

        time_array = np.linspace(0, len(x_values)/SAMPLING_RATE, len(x_values))

    figure = {
        'data': [
            go.Scatter(x=time_array, y=list(x_values), mode='lines', name='X'),
            go.Scatter(x=time_array, y=list(y_values), mode='lines', name='Y'),
            go.Scatter(x=time_array, y=list(z_values), mode='lines', name='Z')
        ],
        'layout': {
            'title': f'Raw Accelerometer Data (Sampling Rate: {SAMPLING_RATE:.2f} Hz)',
            'xaxis': {'title': 'Time (seconds)'},
            'yaxis': {'title': 'Acceleration'},
            'legend': {'orientation': 'h', 'y': 1.1}
        }
    }
    return figure

@app.callback(
    [Output('x-fft-graph', 'figure'),
     Output('y-fft-graph', 'figure'),
     Output('z-fft-graph', 'figure'),
     Output('magnitude-fft-graph', 'figure')],
    Input('interval-component', 'n_intervals')
)
def update_graphs(n):
    if not fft_data_queue.empty():
        global freq_data, x_fft_data, y_fft_data, z_fft_data, magnitude_fft_data
        freq_data, x_fft_data, y_fft_data, z_fft_data, magnitude_fft_data = fft_data_queue.get()

    axis_layout = {
        'xaxis': {
            'title': 'Frequency (Hz)',
            'range': [0, 10] 
        },
        'yaxis': {
            'title': 'Magnitude'
        }
    }
    

    x_fig = {
        'data': [go.Scatter(x=freq_data, y=x_fft_data, mode='lines')],
        'layout': {
            'title': f'FFT of X-axis (Frequency Emphasis: 0.5-10 Hz, Rate: {SAMPLING_RATE:.2f} Hz)',
            **axis_layout
        }
    }
    
    y_fig = {
        'data': [go.Scatter(x=freq_data, y=y_fft_data, mode='lines')],
        'layout': {
            'title': f'FFT of Y-axis (Frequency Emphasis: 0.5-10 Hz, Rate: {SAMPLING_RATE:.2f} Hz)',
            **axis_layout
        }
    }
    
    z_fig = {
        'data': [go.Scatter(x=freq_data, y=z_fft_data, mode='lines')],
        'layout': {
            'title': f'FFT of Z-axis (Frequency Emphasis: 0.5-10 Hz, Rate: {SAMPLING_RATE:.2f} Hz)',
            **axis_layout
        }
    }
    
    magnitude_fig = {
        'data': [go.Scatter(x=freq_data, y=magnitude_fft_data, mode='lines')],
        'layout': {
            'title': f'FFT of Magnitude (sqrt(x²+y²+z²)) (Frequency Emphasis: 0.5-10 Hz, Rate: {SAMPLING_RATE:.2f} Hz)',
            **axis_layout
        }
    }
    
    return x_fig, y_fig, z_fig, magnitude_fig

def update_sampling_rate():
    global SAMPLING_RATE, timestamps
    
    if len(timestamps) < 10:
        return 
    
    time_diffs = []
    for i in range(1, len(timestamps)):
        time_diffs.append(timestamps[i] - timestamps[i-1])
    
    avg_time_diff = sum(time_diffs) / len(time_diffs)
    
    if avg_time_diff > 0:
        new_rate = 1.0 / avg_time_diff
        
        alpha = 0.2 
        SAMPLING_RATE = (alpha * new_rate) + ((1 - alpha) * SAMPLING_RATE)
        
        print(f"Updated sampling rate: {SAMPLING_RATE:.2f} Hz (average time diff: {avg_time_diff*1000:.2f} ms)")

def perform_fft():
    global x_values, y_values, z_values, magnitude_values, SAMPLING_RATE
    

    update_sampling_rate()

    x_array = np.array(list(x_values)[-100:])
    y_array = np.array(list(y_values)[-100:])
    z_array = np.array(list(z_values)[-100:])
    magnitude_array = np.array(list(magnitude_values)[-100:])
    
    if len(x_array) < 50: 
        return
    
    n_fft = 128
    

    if len(x_array) < n_fft:
        x_array = np.pad(x_array, (0, n_fft - len(x_array)), 'constant')
        y_array = np.pad(y_array, (0, n_fft - len(y_array)), 'constant')
        z_array = np.pad(z_array, (0, n_fft - len(z_array)), 'constant')
        magnitude_array = np.pad(magnitude_array, (0, n_fft - len(magnitude_array)), 'constant')
    
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
 
    freq = np.fft.fftfreq(sample_count, d=1/SAMPLING_RATE)

    positive_freq_indices = np.where(freq >= 0)[0]
    freq = freq[positive_freq_indices]

    x_fft_magnitude = np.abs(x_fft)[positive_freq_indices]
    y_fft_magnitude = np.abs(y_fft)[positive_freq_indices]
    z_fft_magnitude = np.abs(z_fft)[positive_freq_indices]
    magnitude_fft_magnitude = np.abs(magnitude_fft)[positive_freq_indices]
    

    x_fft_magnitude = x_fft_magnitude / sample_count
    y_fft_magnitude = y_fft_magnitude / sample_count
    z_fft_magnitude = z_fft_magnitude / sample_count
    magnitude_fft_magnitude = magnitude_fft_magnitude / sample_count

    min_freq = 0.5
    max_freq = 10.0
    emphasis_start = 7.0 

    scaling = np.ones_like(freq)
    

    below_min = freq < min_freq
    in_range = (freq >= min_freq) & (freq <= max_freq)
    above_emphasis = (freq > emphasis_start) & (freq <= max_freq)
    above_max = freq > max_freq
    

    scaling[below_min] = np.exp((freq[below_min] - min_freq) * 2)
    

    scaling[above_emphasis] = 1.0 + ((freq[above_emphasis] - emphasis_start) / 
                                    (max_freq - emphasis_start)) * 2.0
    

    scaling[above_max] = np.exp(-(freq[above_max] - max_freq) * 0.5)
    

    x_fft_filtered = x_fft_magnitude * scaling
    y_fft_filtered = y_fft_magnitude * scaling
    z_fft_filtered = z_fft_magnitude * scaling
    magnitude_fft_filtered = magnitude_fft_magnitude * scaling
    

    expected_range = (freq >= 4.0) & (freq <= 6.0)
    if np.any(expected_range):
        mag_in_range = magnitude_fft_filtered[expected_range]
        if len(mag_in_range) > 0:
            peak_idx = np.argmax(mag_in_range) + np.where(expected_range)[0][0]
            peak_freq = freq[peak_idx]
            peak_magnitude = magnitude_fft_filtered[peak_idx]
            print(f"Dominant frequency in 4-6 Hz range: {peak_freq:.3f} Hz with magnitude {peak_magnitude:.6f}")
    

    fft_data_queue.put((freq, x_fft_filtered, y_fft_filtered, z_fft_filtered, magnitude_fft_filtered))
    print(f"FFT calculated with rate {SAMPLING_RATE:.2f} Hz using last 100 samples")


async def echo(websocket):
    global message_count, x_values, y_values, z_values, magnitude_values, timestamps

    client_address = websocket.remote_address
    print(f"Client connected: {client_address}")

    try:
        async for message in websocket:
            if len(message) == 12:

                current_time = time.time()
                timestamps.append(current_time)
                
                x, y, z = struct.unpack('<fff', message)

                if message_count % 100 == 0:
                    print(f"Sample {message_count}: x: {x:.2f}, y: {y:.2f}, z: {z:.2f}")
                

                x_values.append(x)
                y_values.append(y)
                z_values.append(z)
                
                magnitude = np.sqrt(x**2 + y**2 + z**2)
                magnitude_values.append(magnitude)
                
                message_count += 1

                if message_count % 2 == 0:
                    update_sampling_rate()

                if message_count % 100 == 0:
                    perform_fft()
                

                if message_count % 1000 == 0:
                    save_to_csv(y_values, message_count)
    except websockets.exceptions.ConnectionClosed:
        print(f"Connection closed for {client_address}")

# Start Dash server in a separate thread
def run_dash_server():
    app.run(debug=False, port=8050)


async def websocket_server():
    async with websockets.serve(echo, "0.0.0.0", 8000):
        print("WebSocket server started on ws://0.0.0.0:8000")
        while True:
            await asyncio.sleep(3600) 

def main():
    # Start Dash server in a separate thread
    dash_thread = threading.Thread(target=run_dash_server)
    dash_thread.daemon = True
    dash_thread.start()
    

    asyncio.run(websocket_server())

if __name__ == "__main__":
    main()
