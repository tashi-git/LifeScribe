from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from db_config import db_config
import datetime
import jwt
from functools import wraps

app = Flask(__name__)
app.secret_key = 'my_secre_key_12345'  # Change this to a secure secret key
CORS(app)  # Allow JS to talk to Flask from same or other origins


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('diary'))
    return redirect(url_for('login'))


def get_db_connection():
    return mysql.connector.connect(**db_config)


# -------- API REGISTER --------
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data['username']
    email = data['email']
    password = generate_password_hash(data['password'])
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, password))
        conn.commit()
        return jsonify({'status': 'success'})
    except mysql.connector.IntegrityError as e:
        if e.errno == 1062:  # Duplicate entry
            return jsonify({'status': 'error', 'message': 'Username or email already exists!'})
        else:
            return jsonify({'status': 'error', 'message': 'Registration failed!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        cur.close()
        conn.close()


# JWT token required decorator
# This decorator checks for a valid JWT token in the Authorization header
# Format: "Bearer <token>"
# If valid, extracts user_id and passes it to the protected function
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get the Authorization header from the request
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            # Extract the token part after "Bearer "
            token = token.split(" ")[1]  # Bearer <token>
            # Decode the JWT token using the app's secret key
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            # Extract user_id from the decoded token
            current_user_id = data['user_id']
        except:
            # If decoding fails, token is invalid
            return jsonify({'message': 'Token is invalid!'}), 401
        # Call the original function with current_user_id as the first argument
        return f(current_user_id, *args, **kwargs)
    return decorated

# -------- API LOGIN --------
# Handles user login via API
# Expects JSON payload with 'username' and 'password'
# Returns JWT token on success for API authentication
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        # Generate JWT token with user_id and 24-hour expiration
        token = jwt.encode({'user_id': user['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.secret_key, algorithm="HS256")
        return jsonify({'status': 'success', 'token': token, 'user_id': user['id']})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials!'})


# -------- ADD DIARY ENTRY --------
# Protected API endpoint to add a new diary entry
# Requires JWT token for authentication
# Expects JSON payload with 'content'
# Sets entry_date to today's date automatically
@app.route('/api/entry', methods=['POST'])
@token_required
def add_entry(current_user_id):
    data = request.get_json()
    content = data['content']
    entry_date = datetime.date.today()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO entries (user_id, content, entry_date) VALUES (%s, %s, %s)", (current_user_id, content, entry_date))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'success'})


# -------- GET ENTRIES --------
# Protected API endpoint to retrieve user's diary entries
# Requires JWT token for authentication
# Returns list of entries ordered by creation date (newest first)
@app.route('/api/entries', methods=['GET'])
@token_required
def get_entries(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM entries WHERE user_id=%s ORDER BY created_at DESC", (current_user_id,))
    entries = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(entries)


# -------- LOGIN PAGE --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            token = jwt.encode({'user_id': user['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.secret_key, algorithm="HS256")
            session['token'] = token
            return redirect(url_for('diary'))
        else:
            return render_template('login.html', error='Invalid credentials!')
    return render_template('login.html')


# -------- REGISTER PAGE --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, password))
            conn.commit()
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            return render_template('register.html', error='Username or email already exists!')
        finally:
            cur.close()
            conn.close()
    return render_template('register.html')


# -------- DIARY PAGE --------
@app.route('/diary')
def diary():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT username, email FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('diary.html', user_id=session['user_id'], username=user['username'], email=user['email'])


# -------- ADD ENTRY --------
@app.route('/entry', methods=['POST'])
def add_entry_form():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = request.form['content']
    entry_date = request.form['entry_date']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO entries (user_id, content, entry_date) VALUES (%s, %s, %s)", (session['user_id'], content, entry_date))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('diary'))


# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('token', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
