import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_NAME = 'users.db'

# Create the database and users table
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
        ''')
        # Create a default admin user
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "password123"))
        except sqlite3.IntegrityError:
            pass  # user already exists

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = cur.fetchone()
        if user:
            return redirect(url_for('home'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            try:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                message = 'Registration successful! You can now log in.'
            except sqlite3.IntegrityError:
                message = 'Username already exists. Please choose a different one.'
    return render_template('register.html', message=message)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/task_manager')
def task_manager():
    return render_template('Task_manager.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
