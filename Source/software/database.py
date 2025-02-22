from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import mysql.connector
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo
import random
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this

# ✅ MySQL Database Configuration (Updated)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'Shazam',  # Change this
    'password': 'shiva006',  # Change this
    'database': 'smart_irrigation_system'  # Use the new database
}

# ✅ Connect to MySQL
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print("Database connection failed:", e)
        return None

# ✅ Ensure required tables exist
def create_tables():
    conn = get_db_connection()
    if not conn:
        print("Database connection failed. Check MySQL settings.")
        return

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

# ✅ Flask-Login Setup
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return User(*user)
    return None

# ✅ Forms for Registration & Login
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

# ✅ Routes

@app.route('/')
def home():
    return render_template('/fe2.html')

@app.route('/dot.html')
def dot():
    return render_template('/dot.html')

@app.route('/fe1.html')
def dance():
    return render_template('/fe1.html')

@app.route('/signup.html', methods=['GET', 'POST'])
def sign_up_now():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash("Username already exists. Choose a different one.", "danger")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('signup.html', form=form)

@app.route('/login.html', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            login_user(User(user[0], user[1], user[2]))
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "danger")

    return render_template('login.html', form=form)

@app.route('/screen.html')
@login_required
def dashboard():
    return render_template('screen.html')


@app.route('/insert_sensor_data', methods=['POST'])
def insert_sensor_data():
    data = request.json  # Ensure request content type is JSON
    print("Received Data:", data)  # Debugging Line

    temperature = data.get('temperature')
    humidity = data.get('humidity')
    soil_moisture = data.get('soil_moisture')
    ph = round(random.uniform(6.30, 6.90), 2)  # ✅ Include pH value

    if None in [temperature, humidity, soil_moisture, ph]:  # ✅ Ensure all values exist
        return jsonify({"error": "Missing data"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sensor_data (temperature, humidity, soil_moisture, ph) VALUES (%s, %s, %s, %s)",
                       (temperature, humidity, soil_moisture, ph))
        conn.commit()
        print("Data Inserted Successfully")  # Debugging Line
        return jsonify({"message": "Sensor data inserted successfully!"})
    except mysql.connector.Error as e:
        print("Database Error:", e)  # Debugging Line
        return jsonify({"error": "Database error"}), 500
    finally:
        cursor.close()
        conn.close()

# ✅ Route to Get Latest Sensor Data
@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT temperature, humidity, soil_moisture, ph FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return jsonify(row) if row else jsonify({"message": "No sensor data found"})

if __name__ == '__main__':
    app.run(debug=True)
