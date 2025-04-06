from flask import Flask, render_template, jsonify
import os
import random

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))

def get_sensor_data():
    return {
        "temperature": round(random.uniform(15, 30), 2),
        "humidity": round(random.uniform(30, 70), 2),
        "light": round(random.uniform(100, 1000), 2)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    return jsonify(get_sensor_data())

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
