import paho.mqtt.client as mqtt
import threading
import time
import json
from collections import deque
from flask import Flask, jsonify, render_template
from flask_cors import CORS

# MQTT Configuration
mqtt_broker = "192.168.8.176"
mqtt_port = 1883
client_list = []
last_update = 0

# Sensor history for temporal logic (store last N seconds)
history_duration = 120  # seconds
sensor_history = deque(maxlen=history_duration)

# Flask app setup
app = Flask(__name__, template_folder='templates')
CORS(app)

# Current sensor data
sensor_data = {
    "temperature": 0,
    "humidity": 0,
    "gas": 0
}

# MQTT client setup
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("/client/request")
    client.subscribe("/client/data")

def on_message(client, userdata, msg):
    global sensor_data, last_update
    try:
        if msg.topic == "/client/request":
            client_name = msg.payload.decode("utf-8")
            if client_name not in client_list:
                client_list.append(client_name)
            print(f"Received request from {client_name}")
            client.publish(f"/client/response/{client_name}", "start_comm")
        
        elif msg.topic == "/client/data":
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)
            print(f"Received sensor data: {data}")
            
            # Update sensor data
            sensor_data.update({
                "temperature": data.get("temperature", sensor_data["temperature"]),
                "humidity": data.get("humidity", sensor_data["humidity"]),
                "gas": data.get("gas", sensor_data["gas"])
            })
            
            last_update = time.time()
            
    except Exception as e:
        print(f"Error processing message: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(mqtt_broker, mqtt_port, 60)

def run_mqtt():
    while True:
        mqtt_client.loop()
        time.sleep(0.1)

def process_temporal_data():
    while True:
        now = time.time()
        current_snapshot = {
            "timestamp": now,
            "temperature": sensor_data["temperature"],
            "humidity": sensor_data["humidity"],
            "gas": sensor_data["gas"]
        }
        sensor_history.append(current_snapshot)
        time.sleep(1)

def compute_averages(duration=30):
    now = time.time()
    recent_data = [entry for entry in sensor_history if now - entry["timestamp"] <= duration]

    if not recent_data:
        return {
            "avg_temperature": 0,
            "avg_humidity": 0,
            "avg_gas": 0
        }

    avg_temp = sum(d["temperature"] for d in recent_data) / len(recent_data)
    avg_humidity = sum(d["humidity"] for d in recent_data) / len(recent_data)
    avg_gas = sum(d["gas"] for d in recent_data) / len(recent_data)

    return {
        "avg_temperature": round(avg_temp, 2),
        "avg_humidity": round(avg_humidity, 2),
        "avg_gas": round(avg_gas, 2)
    }

# Flask routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/data')
def get_data():
    avg_data = compute_averages(duration=30)  # Change window if needed
    return jsonify({
        "current": sensor_data,
        "averages": avg_data,
        "last_update": last_update
    })

if __name__ == "__main__":
    # Start MQTT thread
    threading.Thread(target=run_mqtt, daemon=True).start()
    threading.Thread(target=process_temporal_data, daemon=True).start()
    print("MQTT server running...")
    
    # Start Flask web server
    print("Starting web server...")
    app.run(host='0.0.0.0', port=5000, threaded=True)
