from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import calendar
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for sessions

# Initialize DB
def init_db():
    with sqlite3.connect('app.db') as conn:
        # Users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
        ''')
        # To-do tasks table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                is_done BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        # Events table for calendar
        conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                title TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')

        # Create default admin user
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "password123"))
        except sqlite3.IntegrityError:
            pass  # admin already exists

# Helper function to get events for user/month
def get_user_events(user_id, year, month):
    with sqlite3.connect('app.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT day, title FROM events
            WHERE user_id = ? AND year = ? AND month = ?
        ''', (user_id, year, month))
        return {day: title for day, title in cur.fetchall()}

# Home
@app.route('/')
def home():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('app.db') as conn:
            try:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                message = 'Registration successful!'
            except sqlite3.IntegrityError:
                message = 'Username already exists.'
    return render_template('register.html', message=message)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('app.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
            user = cur.fetchone()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('task'))
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Task list (only for logged-in users)
@app.route('/task')
def task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect("app.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, task, is_done FROM todos WHERE user_id = ?", (session['user_id'],))
        tasks = cur.fetchall()
    return render_template('Task_manager.html', tasks=tasks)

# Add task
@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    task = request.form['task']
    if task:
        with sqlite3.connect("app.db") as conn:
            conn.execute("INSERT INTO todos (user_id, task) VALUES (?, ?)", (session['user_id'], task))
    return redirect(url_for('task'))

# Delete task
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect("app.db") as conn:
        conn.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    return redirect(url_for('task'))

# Calendar view showing current month + user events
@app.route('/calendar')
def calendar_view():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    now = datetime.now()
    year, month = now.year, now.month

    cal = calendar.monthcalendar(year, month)
    events = get_user_events(session['user_id'], year, month)

    return render_template('calendar.html', year=year, month=month, cal=cal, events=events)

# Add calendar event (GET shows form, POST adds event)
@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    message = None
    if request.method == 'POST':
        year = int(request.form['year'])
        month = int(request.form['month'])
        day = int(request.form['day'])
        title = request.form['title']

        with sqlite3.connect('app.db') as conn:
            conn.execute('''
                INSERT INTO events (user_id, year, month, day, title)
                VALUES (?, ?, ?, ?, ?)
            ''', (session['user_id'], year, month, day, title))
        message = "Event added!"

    now = datetime.now()
    return render_template('add_event.html', message=message, year=now.year, month=now.month)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)


