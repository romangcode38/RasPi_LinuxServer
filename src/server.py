import paho.mqtt.client as mqtt
import threading
import time
import json
from flask import Flask, jsonify, render_template  # Added render_template here
from flask_cors import CORS

# MQTT Configuration
mqtt_broker = "192.168.8.176"
mqtt_port = 1883
client_list = []
sensor_data = {
    "temperature": 0,
    "humidity": 0,
    "light": 0  # This will remain 0 unless you add a light sensor
}
last_update = 0

# Flask Web Server
app = Flask(__name__, template_folder='templates')
CORS(app)  # Enable CORS for all routes

# MQTT Client Setup
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
                # Light remains unchanged unless provided
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/data')
def get_data():
    return jsonify({
        "temperature": sensor_data["temperature"],
        "humidity": sensor_data["humidity"],
        "light": sensor_data["light"],
        "last_update": last_update
    })

if __name__ == "__main__":
    # Start MQTT thread
    threading.Thread(target=run_mqtt, daemon=True).start()
    print("MQTT server running...")
    
    # Start Flask web server
    print("Starting web server...")
    app.run(host='0.0.0.0', port=5000, threaded=True)