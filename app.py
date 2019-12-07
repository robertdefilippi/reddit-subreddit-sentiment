import os
import time
import json
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import generate_password_hash, check_password_hash

import psycopg2

from flask import Flask, render_template, request, jsonify, url_for, redirect, session, make_response, flash

import logging

from os.path import exists
from os import makedirs

import get_reddit_data
import pg_manager

# Global variables

MAX_ROWS = 9000
COOKIE_TIME_OUT = 60*5
SECRET_KEY = '-j4uXaJVQXohwtelyPkr4A'

# Start app and get credentials

db = pg_manager.DBConnect()
db.set_credentials_and_connections()

# Main app and logging instance

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
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
    scheduler.add_job(func=check_did_write, trigger="interval", minutes=30, misfire_grace_time=10)
    scheduler.start()
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

###############
# App functions
###############

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
    app.logger.info(f'Subreddit: {subreddit_name}')
    app.logger.info(f'Data values: {data_values}')
    app.logger.info(f'Post handled: {request.json}')
    return jsonify({'payload':json.dumps({'data_values':data_values})})

@app.route('/update_hist_values')
def update_hist():
    subreddit_name = request.args.get('vals')
    histogram_counts = db.get_histogram_counts(subreddit_name)
    
    app.logger.info(f'Post handled: {request.json}')
    return jsonify({'payload':json.dumps({'histogram_counts':histogram_counts})})

@app.route('/submit_login', methods=['POST'])
def submit_login():	
    app.logger.info("Login submission")
    request_dict = request.form.to_dict()   
    
    form_email = request_dict.get('email-login', None)
    from_password = request_dict.get('password-login', None)

    session_email = session.get('email', None)
    
    if session_email:
        # Users has session
        app.logger.info("Received email from login")
        password_hash = db.get_user_password_hash(form_email)

        verify_user = check_password_hash(password_hash, from_password)
        
        if verify_user:
            app.logger.info("User password verified. Redirecting to dashboard.")
            session['email'] = session_email
            return redirect('/dashboard')
        
        else:
            app.logger.info("Invalid email/password!")
            flash('Invalid email/password!')
            return redirect('/login')
            
    elif form_email and from_password:
        app.logger.info("User does not have session. Checking password.")
        password_hash = db.get_user_password_hash(form_email)
        
        if password_hash:
            app.logger.info("Verifying user")
            verify_user = check_password_hash(password_hash, from_password)
        
            if verify_user:
                app.logger.info("User verified. Redirecting to dashbaord")
                session['email'] = form_email
                resp = make_response(redirect('/dashboard'))
                return resp
            
            else:
                app.logger.info("'Invalid password!'")
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
    app.logger.info(f"Regisration submission: {request.form}")
    _email = request.form['email-register']
    _password = request.form['password-register']

    does_user_exist = db.check_if_exists(_email)

    if does_user_exist:
        flash('User already exists ... try logging in')
        return render_template('login.html')

    else:
        _password_hash = generate_password_hash(_password)
        # Set session
        session['email'] = _email
        app.logger.info(f"Session set for: {_email}")

        # Create new user
        db.create_new_user(_email, _password_hash)
        
        flash('Successfully created a new users!')
        return render_template('login.html')


@app.route('/logout')
def logout():
    
    session_email = session.get('email', None)
	
    if session_email:
        session.pop('email', None)
    flash('Logged out')
    return redirect('login')

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

###############
# Routes
###############

@app.route('/', methods=['GET', 'POST'])
def login_auth():
    
    session_email = session.get('email', None)
    app.logger.info(f'Checking email {session_email} for session')   
    
    password_hash = db.get_user_password_hash(session_email) if session_email else None
    
    if session_email and password_hash:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    session_email = session.get('email', None)
    
    if session_email:
        return redirect(url_for(''))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    session_email = session.get('email', None)
    
    if session_email:
        return redirect(url_for(''))
    return render_template('register.html')
    
@app.route('/dashboard')
def homepage():
    session_email = session.get('email', None)
    
    if session_email:
        return render_template("dashboard.html")
    else:
        flash('Login required')
        return render_template('login.html')
    
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404		

@app.route('/shutdown', methods=['GET'])
def shutdown():
    app.logger.info(f'Forcing Shutdown: {request.json}')
    atexit.register(lambda: scheduler.shutdown())
    shutdown_server()
    shutdown_message = 'Server shutting down...'
    
    return shutdown_message

########################################################

if __name__ == "__main__":
    app.logger.info(f'Starting App ...')
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.secret_key = os.urandom(12)
    # app.run(debug=True, host="localhost", port=8000)
    # init_scheduler()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)