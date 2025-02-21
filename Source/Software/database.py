from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import mysql.connector
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a secure key

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'Shazam',  # Change this to your MySQL username
    'password': 'shiva006',  # Change this to your MySQL password
}

# Connect to MySQL (Create DB if not exists)
def get_db_connection(database=None):
    config = DB_CONFIG.copy()
    if database:
        config['database'] = database
    return mysql.connector.connect(**config)

def create_database(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {username}")
    cursor.close()
    conn.close()

def create_users_table(username):
    conn = get_db_connection(username)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(150) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            temperature FLOAT NOT NULL,
            humidity FLOAT NOT NULL,
            soil_moisture FLOAT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection('default_db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(*user)
    return None

# Forms
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        create_database(username)  # Create database for user
        create_users_table(username)  # Create necessary tables

        conn = get_db_connection(username)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username already exists. Choose a different one.', 'danger')
        else:
            hashed_password = generate_password_hash(form.password.data)
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        conn.close()
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        conn = get_db_connection(username)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], form.password.data):
            login_user(User(*user))
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Sensor Data Routes
@app.route('/insert_sensor_data', methods=['POST'])
def insert_sensor_data():
    data = request.json
    username = data.get('username')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    soil_moisture = data.get('soil_moisture')

    conn = get_db_connection(username)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sensor_data (temperature, humidity, soil_moisture) VALUES (%s, %s, %s)", (temperature, humidity, soil_moisture))
    conn.commit()
    conn.close()

    return jsonify({"message": "Sensor data inserted successfully!"})

@app.route('/get_latest_sensor_data', methods=['GET'])
def get_latest_sensor_data():
    username = request.args.get('username')
    conn = get_db_connection(username)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return jsonify(row) if row else jsonify({"message": "No sensor data found"})


CSV_PATH = "soil_moisture_data (1).csv"

def train_model_from_csv():
    """Train the DecisionTreeRegressor model using CSV data."""
    if not os.path.exists(CSV_PATH):
        return None  # Return None if the CSV file doesn't exist

    df = pd.read_csv(CSV_PATH)

    # Ensure required columns exist
    if not all(col in df.columns for col in ['x_coord', 'y_coord', 'soil_moisture']):
        raise ValueError("CSV must contain 'x_coord', 'y_coord', and 'soil_moisture' columns.")

    # Extract features and target
    X = df[['x_coord', 'y_coord']]
    y = df['soil_moisture']

    # Train model
    model = DecisionTreeRegressor()
    model.fit(X, y)
    return model

# Train the model initially
model = train_model_from_csv()

@app.route('/predict_soil_moisture', methods=['POST'])
def predict_soil_moisture():
    """Predict soil moisture based on X, Y coordinates from CSV-trained model."""
    if model is None:
        return jsonify({"error": "Model not trained. Ensure 'data.csv' is present."}), 500

    data = request.json
    x_coord = data.get('x_coord')
    y_coord = data.get('y_coord')

    if x_coord is None or y_coord is None:
        return jsonify({"error": "Missing X or Y coordinate"}), 400

    # Convert input to NumPy array for prediction
    features = np.array([[x_coord, y_coord]])
    predicted_soil_moisture = model.predict(features)[0]

    return jsonify({"predicted_soil_moisture": predicted_soil_moisture})


if __name__ == '__main__':
    app.run(debug=True)

