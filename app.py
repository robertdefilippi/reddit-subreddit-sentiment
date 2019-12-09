# pylint: disable=no-member

import os
import time
import json
import atexit

from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import generate_password_hash, check_password_hash

import psycopg2

from flask import Flask, render_template, request, jsonify, url_for, redirect, session, make_response, flash

import logging

from os.path import exists
from os import makedirs

from src import get_reddit_data
from src import pg_manager

"""Reddit Sentiment App

Provides a histogram distribution of post titles from various subreddits to see 
if they have more positive, negative, or neutral posting titles. 

Each post is given a sentiment score between -1 and 1. The closer the score is 
to 1 the more positive the post title is, the closer to -1 the more negative. 
A score of 0 is a neutral. The analysis of the post is done through the nltk 
package to determine the post title's sentiment.

Ex.
Title: Square Roots of Living Beings
Score: 0 

Title: The best present!
Score: 0.6696

Title: Deaf child gets bullied constantly at this school ... 
Score: -0.6858

The histogram is generated by counting and binning each of the individual 
sentiment scores for various subreddits. 

Author: Robert DeFilippi
"""

# Global variables

MAX_ROWS = 8900
COOKIE_TIME_OUT = 60*5
SECRET_KEY = os.urandom(12)
SESSION_LENGTH_MINUTES = 5

# Start app and get credentials

db = pg_manager.DBConnect()
db.set_credentials_and_connections()

# Main app and logging

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
logging.basicConfig(level=logging.DEBUG)

###############
# App functions
###############


def write_reddit_data() -> None:
    """
    Get sentiment data from Reddit and write to the database.
    """

    list_of_tuples = get_reddit_data.get_subreddit_data()
    db.write_bulk(list_of_tuples)

    # Remove duplicates
    db.remove_duplicates()

    app.logger.info('Completed Writing Data')


def check_did_write() -> None:
    """
    Check if there has been a write to the database in the last
    30 minutes, and if the database is close to full. If there
    has been a write recently, skip writing to the db. If the database
    is close to full then clear older entries.
    """
    app.logger.info(f'Checking data ...')
    did_write = db.did_write_this_hour()
    number_rows = db.get_total_records()

    is_less_nine_thousand_rows = number_rows <= MAX_ROWS

    if not is_less_nine_thousand_rows:
        app.logger.info('Over max number of rows. Removing some random rows.')
        db.delete_oldest_two_datetime()

    if did_write and is_less_nine_thousand_rows:
        app.logger.info('Not writing data.')
    else:
        app.logger.info('Writing data.')
        write_reddit_data()

def get_data_values(subreddit_name: str) -> list:
    """
    Get values for the histogram graph, from a specific subreddit. 

    Args:
        subreddit_name (str): The subreddit to get the values from

    Returns:
        list: A list of values for the sentiment histogram.
    """
    return db.get_histogram_data(subreddit_name)


@app.before_request
def make_session_permanent() -> None:
    """
    Set how long a session should be
    """
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=SESSION_LENGTH_MINUTES)


@app.route('/get_data')
def get_data():
    """
    Route to get the data for the front end of the application.

    Returns:
        flask.Response: response object with data values
    """
    subreddit_name = request.args.get('vals')
    data_values, data_labels, subreddit_name = get_data_values(subreddit_name)
    return jsonify({'payload': json.dumps({'data_values': data_values, 'data_labels': data_labels, 'subreddit_name': subreddit_name})})


@app.route('/update_rows', methods=['GET'])
def update_rows():
    """
    Route to show random rows (posts) from the selected subreddit
    for the front end of the application.

    Returns:
        flask.Response: response object with data values
    """
    subreddit_name = request.args.get('vals')
    data_labels = db.get_random_rows(subreddit_name)
    return jsonify({'payload': json.dumps({'data_labels': data_labels})})


@app.route('/update_select')
def update_select():
    """
    Route to update the values in the "select" dropdown
    on the front of the application.

    Returns:
        flask.Response: response object with data values
    """
    data_labels = db.get_unique_categories()
    return jsonify({'payload': json.dumps({'data_labels': data_labels})})


@app.route('/get_select_value', methods=['POST'])
def submit_handler():
    """
    Route to update the values in the "select" dropdown
    on the front of the application.

    Returns:
        flask.Response: response object with data values
    """
    app.logger.info(f'Post handled: {request.json}')
    return request.json


@app.route('/update_card_values')
def update_cards():
    """
    Update the four cards at the top of the application with new values
    when new data is retrieved from Reddit.

    Returns:
        flask.Response: response object with data values
    """
    subreddit_name = request.args.get('vals')
    data_values = db.get_card_counts(subreddit_name)
    app.logger.info(f'Subreddit: {subreddit_name}')
    app.logger.info(f'Data values: {data_values}')
    app.logger.info(f'Post handled: {request.json}')
    return jsonify({'payload': json.dumps({'data_values': data_values})})


@app.route('/update_hist_values')
def update_hist():
    """
    Update the the graph in with new values.

    Returns:
        flask.Response: response object with data values
    """
    subreddit_name = request.args.get('vals')
    histogram_counts = db.get_histogram_counts(subreddit_name)

    app.logger.info(f'Post handled: {request.json}')
    return jsonify({'payload': json.dumps({'histogram_counts': histogram_counts})})


@app.route('/submit_login', methods=['POST'])
def submit_login():
    """
    Submit login information, and check: 
        1) Does the user exists, and;
        2) Is the password is correct.

    If the user checks out, then login the user.

    Returns:
        flask.Response: response object with data values
    """
    app.logger.info("Login submission")
    request_dict = request.form.to_dict()

    form_email = request_dict.get('email-login', None)
    from_password = request_dict.get('password-login', None)

    session_email = session.get('email', None)

    # Check if the users already has a session saved
    if session_email:

        app.logger.info("Received email from login")
        password_hash = db.get_user_password_hash(form_email)

        verify_user = check_password_hash(password_hash, from_password)

        # Check if user password is correct
        if verify_user:
            app.logger.info(
                "User password verified. Redirecting to dashboard.")
            session['email'] = session_email
            return redirect('/dashboard')

        else:
            app.logger.info("Invalid email/password!")
            flash('Invalid email/password!')
            return redirect('/login')

    # Check if user password is correct, if they don't have a session already
    elif form_email and from_password:
        app.logger.info("User does not have session. Checking password.")
        password_hash = db.get_user_password_hash(form_email)

        # Check hashed password
        if password_hash:
            app.logger.info("Verifying user")
            verify_user = check_password_hash(password_hash, from_password)

            if verify_user:
                app.logger.info("User verified. Redirecting to dashbaord")
                session['email'] = form_email
                resp = make_response(redirect('/dashboard'))
                return resp

            else:
                app.logger.info("Invalid password!")
                flash('Invalid password!')
                return redirect('/login')

        else:
            app.logger.info("Invalid email/password!")
            flash('Invalid email/password!')
            return redirect('/login')

    else:
        app.logger.info("Invalid email/password!")
        flash('Invalid email/password!')
        return redirect('/login')


@app.route('/register_user', methods=['POST'])
def register_user():
    """
    Submit user registration information, and check: 
        1) Does the user already exist in the data base, and;
        2) Is the password correct.

    If the submitted information checks out, create a new user.

    Returns:
        flask.Response: response object with data values
    """
    app.logger.info(f"Regisration submission: {request.form}")
    _email = request.form['email-register']
    _password = request.form['password-register']

    does_user_exist = db.check_if_exists(_email)

    if does_user_exist:
        flash('User already exists ... try logging in')
        return render_template('login.html')

    else:
        # Save a HASHED version of the password in the database
        _password_hash = generate_password_hash(_password)

        # Set session for user
        session['email'] = _email
        app.logger.info(f"Session set for: {_email}")

        # Create new user
        db.create_new_user(_email, _password_hash)

        flash('Successfully created a new users!')
        return render_template('login.html')


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

###############
# Scheduling
###############


scheduler = BackgroundScheduler()
scheduler.add_job(func=check_did_write, trigger="interval",
                  minutes=30, misfire_grace_time=10)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

###############
# Routes
###############


@app.route('/', methods=['GET', 'POST'])
def login_auth():
    """
    Main page routing of the application. Checks if the user has a current session
    and if so, move to the dashboard. If there is no session then 
    prompt the user to log in.

    Returns:
        flask.Response: response object with data values
    """

    scheduler.print_jobs()

    session_email = session.get('email', None)
    app.logger.info(f'Checking email {session_email} for session')

    password_hash = db.get_user_password_hash(
        session_email) if session_email else None

    if session_email and password_hash:
        return render_template("dashboard.html")
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route to prompt the user to login if there is no session.

    Returns:
        flask.Response: response object with data values
    """
    session_email = session.get('email', None)

    app.logger.info(f'Checking email {session_email} for session')

    if session_email:
        return render_template("dashboard.html")
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Logout the user, and remove the session.

    Returns:
        flask.Response: response object with data values
    """

    session_email = session.get('email', None)

    if session_email:
        session.pop('email', None)
    flash('Logged out')
    return redirect('login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register route to prompt the user to register.

    Returns:
        flask.Response: response object with data values
    """
    session_email = session.get('email', None)

    if session_email:
        return render_template('login.html')
    return render_template('register.html')


@app.route('/dashboard')
def homepage():
    """
    Dashboard route to prompt the user to register.

    Returns:
        flask.Response: response object with data values
    """
    session_email = session.get('email', None)

    if session_email:
        return render_template("dashboard.html")
    else:
        flash('Login required')
        return render_template('login.html')


@app.errorhandler(404)
def not_found(error):
    """
    If there is a error on any of the routes, render a 404 page.

    Returns:
        flask.Response: response object with data values
    """
    return render_template("404.html"), 404


@app.route('/shutdown', methods=['GET'])
def shutdown():
    """
    Force a shutdown the of application.

    Returns:
        flask.Response: response object with data values
    """
    app.logger.info(f'Forcing Shutdown: {request.json}')
    shutdown_server()
    shutdown_message = 'Server shutting down...'

    return shutdown_message


if __name__ == "__main__":
    app.logger.info(f'Starting App ...')
    app.run(threaded=True, use_reloader=False)
