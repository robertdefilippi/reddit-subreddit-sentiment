import os
import time
import json
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

import psycopg2

from flask import Flask, render_template, request, jsonify, url_for, redirect
import logging

from os.path import exists
from os import makedirs

import get_reddit_data
import pg_manager

MAX_ROWS = 9000

# Start app and get credentials

db = pg_manager.DBConnect()
db.set_credentials_and_connections()

# Main app and logging instance

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Functions for interacting with app

def write_reddit_data():
    
    list_of_tuples = get_reddit_data.get_subreddit_data()
    db.write_bulk(list_of_tuples)

    # Remove duplicates
    db.remove_duplicates()

    app.logger.info('Completed Writing Data')

def check_did_write():
    app.logger.info(f'Checking data ...')
    did_write = db.did_write_this_hour()
    number_rows = db.get_total_records()

    is_less_nine_thousand_rows = number_rows <= MAX_ROWS

    if not is_less_nine_thousand_rows:
        db.delete_oldest_two_datetime()
    
    if did_write and is_less_nine_thousand_rows:
        app.logger.info('Not writing data.')
    else:
        app.logger.info('Writing data.')
        write_reddit_data()

def get_data_values(subreddit_name):
    return db.get_histogram_data(subreddit_name)

@app.before_first_request
def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_did_write, trigger="interval", minutes=30)
    scheduler.start()
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

init_scheduler()

# App functions

@app.route('/get_data')
def get_data():
    subreddit_name = request.args.get('vals')
    data_values, data_labels, subreddit_name = get_data_values(subreddit_name)
    return jsonify({'payload':json.dumps({'data_values':data_values, 'data_labels':data_labels, 'subreddit_name': subreddit_name})})

@app.route('/update_rows', methods=['GET'])
def update_rows():
    subreddit_name = request.args.get('vals')
    data_labels = db.get_random_rows(subreddit_name)
    return jsonify({'payload': json.dumps({'data_labels':data_labels})})

@app.route('/update_select')
def update_select():
    data_labels = db.get_unique_categories()
    return jsonify({'payload': json.dumps({'data_labels':data_labels})})

@app.route('/get_select_value', methods=['POST'])
def submit_handler():
    app.logger.info(f'Post handled: {request.json}')
    return request.json

@app.route('/update_card_values')
def update_cards():
    subreddit_name = request.args.get('vals')
    data_values = db.get_card_counts(subreddit_name)
    print(subreddit_name, data_values)
    app.logger.info(f'Post handled: {request.json}')
    return jsonify({'payload':json.dumps({'data_values':data_values})})

@app.route('/update_hist_values')
def update_hist():
    subreddit_name = request.args.get('vals')
    histogram_counts = db.get_histogram_counts(subreddit_name)
    
    app.logger.info(f'Post handled: {request.json}')
    return jsonify({'payload':json.dumps({'histogram_counts':histogram_counts})})


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

# Templates

# TODO: Update login screen
@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/')
def homepage():
    return render_template("dashboard.html")

@app.route('/shutdown', methods=['GET'])
def shutdown():
    app.logger.info(f'Forcing Shutdown: {request.json}')
    # atexit.register(lambda: scheduler.shutdown())
    shutdown_server()
    shutdown_message = 'Server shutting down...'
    
    return shutdown_message

############################

if __name__ == "__main__":
    app.logger.info(f'Starting App ...')
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    # app.run(debug=True, host="localhost", port=8888)
    app.run(threaded=True)