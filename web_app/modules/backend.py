import datetime
import os
import logging
import requests
from deep_translator import GoogleTranslator
import json
from dotenv import load_dotenv, dotenv_values
import matplotlib as mpl
import matplotlib.pylab as plt
from flask import abort
from boto3.session import Session

load_dotenv()
cache = os.getenv("cache")
history_dir = "static/history"
API_KEY = os.getenv("API_KEY")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_DYNAMODB_ACCESS_KEY = "AWS_DYNAMODB_ACCESS_KEY"
AWS_DYNAMODB_SECRET_KEY = "AWS_DYNAMODB_SECRET_KEY"



def list_history():
    files = [f for f in os.listdir(history_dir)]
    return files


def save_history(location):
    date = str(datetime.datetime.today().date())
    history_file = {"date": date, "city": location}
    with open(f'{history_dir}/{location}.json', 'w') as fileobj:
        json.dump(history_file, fileobj)



def save_data_to_dynamo(weather_json_data):
    session = Session(aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_KEY,
                      region_name='eu-north-1')

    weather_json_data = json.dumps(weather_json_data)
    new_dict = {}
    database = session.resource('dynamodb')
    table = database.Table('weather-app-database')
    # "data" is the primary key of my table in dynamodb
    new_dict["data"] = weather_json_data
    table.put_item(Item=new_dict)


def download_from_s3():
    session = Session(aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_KEY,
                      region_name='eu-north-1')
    s3 = session.resource('s3')
    desktop = os.path.expanduser("~/Desktop")
    s3.Bucket('my-static-web-site2').download_file('sky.jpg', f'{desktop}/my_local_sky.jpg')


def create_graph(weather):
    # showing graph of temps during the week.
    mpl.use('agg')
    days = []
    day_temps = []
    night_temps = []
    for index in weather.values():
        days.append(index['date'].split('-')[2])
        day_temps.append(index['morning_temp'])
        night_temps.append(index['evening_temp'])
    plt.xlabel('Days', fontsize=15)
    plt.ylabel('Morning Temps', fontsize=15)
    plt.bar(days, day_temps, tick_label=days, color='lightblue')
    plt.savefig('static/graph_day.png')
    plt.xlabel('Days', fontsize=15)
    plt.ylabel('Evening Temps', fontsize=15)
    plt.bar(days, night_temps, tick_label=days, color='lightblue')
    plt.savefig('static/graph_night.png')


def check_cache(location):
    # Check if folder has more then 10 files
    files = os.listdir(cache)
    files = [os.path.join(cache, x) for x in files]
    files = sorted(files, key=os.path.getmtime)
    if files:
        oldest_file = files[0]
        # Check if at least 10 files in folder - delete the oldest one.
        if len(os.listdir("cache")) >= 11:
            os.remove(oldest_file)
    # Check cache for up-to-date location weather file
    date_today = datetime.datetime.now()
    for file in os.listdir(cache):
        file_path = os.path.join(cache, file)
        file_date = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
        # Check if file is older than today and delete it then continue to not return it
        num = (date_today - file_date).days
        if num >= 1:
            os.remove(file_path)
            continue
        # if location in file.split('.')[0]
        if file.split('.')[0] == location:
            return True
    return False


def get_api_with_user_input(location):
    # Get request to the api, if not 200 then a bad string was entered in the query
    response = requests.request("GET",
                                f'https://weather.visualcrossing.com/VisualCrossingWebServices/'
                                f'rest/services/timeline/{location}/'
                                f'?unitGroup=metric&elements=datetime%2CdatetimeEpoch%2Ctempmax%2Ctempmin%2Ctemp%2'
                                f'Chumidity&include=days%2Chours&key={API_KEY}&contentType=json')

    if response.status_code != 200:
        logging.error(f"Error processing location {location}")
        abort(400, "Need to enter a name")
    json_data = response.json()
    return json_data


def filter_api(json_raw):
    # Return days dict with filtered info and the city name + country
    days = {}
    city = json_raw['resolvedAddress']
    translated_city = GoogleTranslator(source='auto', target='en').translate(city)
    for i in range(7):
        days[i] = {'date': json_raw["days"][i]['datetime'],
                   'morning_temp': json_raw["days"][i]['hours'][7]['temp'],
                   'morning_humidity': json_raw["days"][i]['hours'][7]['humidity'],
                   'evening_temp': json_raw["days"][i]['hours'][19]['temp'],
                   'evening_humidity': json_raw["days"][i]['hours'][19]['humidity']}
    return days, translated_city


def create_json_file(filtered_data):
    # Create file name only from the simple name of the location for caching
    path = filtered_data[1].split(',')[0].lower()
    with open(f'{cache}/{path}.json', 'w') as fileobj:
        json.dump(filtered_data, fileobj)


def read_json_file(location):
    # Return only the days dict, takes only the simple name as file name for caching
    location = location.split(',')[0].lower()
    with open(f'{cache}/{location}.json', 'r') as fileobj:
        data = json.load(fileobj)
    return data
