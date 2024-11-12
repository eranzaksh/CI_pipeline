import os
import time
import logging

import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from prometheus_client import Histogram, make_wsgi_app, Counter
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from modules import backend

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all levels
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file named 'app.log'
        logging.StreamHandler()  # Also log to the console

    ]
)
log = logging.getLogger('werkzeug')
log.getLogger = True
logging.getLogger('matplotlib').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})
REQUEST_COUNT = Counter(
    'app_request_count',
    'Application Request Count',
    ['method', 'endpoint', 'http_status']
)

# REQUEST_LATENCY = Histogram(
#     'app_request_latency_seconds',
#     'Application Request Latency',
#     ['method', 'endpoint']
# )

LOCATION_REQUEST_COUNT = Counter(
    'location_request_count',
    'Application Request Count',
    ['method', 'endpoint', 'http_status', 'location']
)

@app.route("/download")
def download():
    backend.download_from_s3()
    return redirect(url_for("home"))

#@app.route("/history/")
#def show_history():
#    files = backend.list_history()
#    return render_template('history.html', files=files)
@app.route("/save_data/<string:location>")
def save_data(location):
    weather_json_file = backend.read_json_file(location)
    backend.save_data_to_dynamo(weather_json_file)
    return redirect(url_for("display", location=location))

@app.route("/display/<string:location>", methods=["GET", "POST"])
def display(location):
    # start_time = time.time()
    LOCATION_REQUEST_COUNT.labels(request.method, '/display', 200, location).inc()
    logging.info(f"Display data for location: {location}")
    weather_json_file = backend.read_json_file(location)
    backend.create_graph(weather_json_file[0])
    graph_day = url_for('static', filename='graph_day.png')
    graph_night = url_for('static', filename='graph_night.png')
    logging.debug(f"Generated graphs for location: {location}")
    if request.method == "POST":
        action = request.form.get("action")

        if action == "send-email":
            receiver_email = request.form['receiver_email']
            email_service_url = "http://send-email-api:5001/send-email"
            payload = {
                "subject": location,
                "body": weather_json_file[0],
                "receiver_email": receiver_email
            }
            response = requests.post(email_service_url, json=payload)
            if response.status_code != 200:
                logging.info(f"Email failed {response.text}")
                return render_template('error.html', error_message="Failed to send email", error_code=response.status_code)
            if response.status_code == 200:
                logging.info(f"Email sent succesfully {response.status_code}")
                return render_template('display.html', weather=weather_json_file[0],
                        location=weather_json_file[1], graph_day=graph_day, graph_night=graph_night)
            
            return render_template('display.html', weather=weather_json_file[0],
                                   location=weather_json_file[1], graph_day=graph_day, graph_night=graph_night)
        location = location.split(',')[0].lower()
        return redirect(url_for("save_data", location=location))
    # weather_json_file is a list of days and location
    # weather_json_file = backend.read_json_file(location)
    return render_template('display.html', weather=weather_json_file[0],
                           location=weather_json_file[1], graph_day=graph_day, graph_night=graph_night)


@app.route('/', methods=["POST", "GET"])
def home():
    REQUEST_COUNT.labels('GET', '/', 200).inc()
    logging.info("Home endpoint was called")
    bg_color = os.getenv('BG-COLOR', '#ffffff')
    if request.method == "POST":
        location = request.form.get("location").lower()
        #backend.save_history(location)
        if backend.check_cache(location):
            return redirect(url_for("display", location=location))
        else:
            raw_json = backend.get_api_with_user_input(location)
            filtered_json = backend.filter_api(raw_json)
            backend.create_json_file(filtered_json)
            return redirect(url_for("display", location=filtered_json[1]))
    return render_template('home.html', bg_color=bg_color)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
