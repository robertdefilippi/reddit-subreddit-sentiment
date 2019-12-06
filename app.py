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

init_scheduler()

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
    print(subreddit_name, data_values)
    app.logger.info(f'Post handled: {request.json}')
    return jsonify({'payload':json.dumps({'data_values':data_values})})

@app.route('/update_hist_values')
def update_hist():
    subreddit_name = request.args.get('vals')
    histogram_counts = db.get_histogram_counts(subreddit_name)
    
    app.logger.info(f'Post handled: {request.json}')
    return jsonify({'payload':json.dumps({'histogram_counts':histogram_counts})})

# check_password_hash('password_hash', 'password')

@app.route('/submit_login', methods=['POST'])
def submit_login():	
    app.logger.info("Login submission: ", request.form)
    
    _email = request.form['email-login']
    _password = request.form['password-login']

    email = session.get('email',None)
    
    app.logger.info(f"{_email}:: {_password}:: {email}")

    if email:
        password = request.cookies.get('password')

        password_hash = db.get_user_password_hash(email)
        verify_user = check_password_hash(password_hash, password)
        
        if verify_user:
            session['email'] = email
            session['password'] = password_hash
            return redirect('/dashboard')
        
        else:
            flash('Invalid email/password!')
            return redirect('/login')
            
    elif _email and _password:
		#check user exists			
        password_hash = db.get_user_password_hash(_email)
        if password_hash:
            verify_user = check_password_hash(password_hash, password)
            if verify_user:
                session['email'] = _email
                resp = make_response(redirect('/dashboard'))
                resp.set_cookie('email', _email, max_age=COOKIE_TIME_OUT)
                resp.set_cookie('pwd', _password, max_age=COOKIE_TIME_OUT)
                return resp
            
            else:
                flash('Invalid password!')
                return redirect('/login')
        
        else:
            flash('Invalid email/password!')
            return redirect('/login')
    
    else:
        flash('Invalid email/password!')
        return redirect('/login')

@app.route('/register_user', methods=['POST'])
def register_user():
    app.logger.info("Regisration submission: ", request.form)
    _email = request.form['email-register']
    _password = request.form['password-register']
    _password_hash = generate_password_hash(_password)
    
    # Set session
    session['email'] = _email
    app.logger.info("Session set for: ", session['email'])

    # Create new user
    db.create_new_user(_email, _password_hash)

    return render_template('login.html')


@app.route('/logout')
def logout():
    
    session_email = session["email"]
	
    if session_email:
        session.pop('email', None)

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
    return render_template("dashboard.html")

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
    app.run(debug=True, host="localhost", port=8888)
    # app.run(threaded=True, host="localhost", port=8888)