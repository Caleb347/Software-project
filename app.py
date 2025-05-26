from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
from calendar import monthrange
import calendar
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- DATABASE SETUP ---
def init_db():
    with sqlite3.connect('app.db') as conn:
        # Users
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
        ''')

        # To-Do Tasks
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                is_done BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')

        # Calendar Events
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
            pass

# --- HELPERS ---
def get_user_events(user_id, year, month):
    with sqlite3.connect('app.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT day, title FROM events
            WHERE user_id = ? AND year = ? AND month = ?
        ''', (user_id, year, month))
        return {day: title for day, title in cur.fetchall()}

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

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
            return redirect(url_for('home'))
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- TO-DO TASK ROUTES ---

@app.route('/task')
def task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect("app.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, task, is_done FROM todos WHERE user_id = ?", (session['user_id'],))
        tasks = cur.fetchall()
    return render_template('Task_manager.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    task = request.form['task']
    if task:
        with sqlite3.connect("app.db") as conn:
            conn.execute("INSERT INTO todos (user_id, task) VALUES (?, ?)", (session['user_id'], task))
    return redirect(url_for('task'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect("app.db") as conn:
        conn.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    return redirect(url_for('task'))

# --- CALENDAR ROUTE ---

@app.route('/calendar', methods=['GET', 'POST'])
def calendar_view():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    year = request.args.get('year', type=int) or datetime.today().year

    # Handle new event submissions
    if request.method == 'POST':
        month = int(request.form['month'])
        day = int(request.form['day'])
        title = request.form['title']

        with sqlite3.connect('app.db') as conn:
            cur = conn.cursor()
            # Check if an event already exists
            cur.execute('''
                SELECT id FROM events
                WHERE user_id = ? AND year = ? AND month = ? AND day = ?
            ''', (user_id, year, month, day))
            existing = cur.fetchone()

            if existing:
                cur.execute('''
                    UPDATE events SET title = ?
                    WHERE id = ?
                ''', (title, existing[0]))
            else:
                cur.execute('''
                    INSERT INTO events (user_id, year, month, day, title)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, year, month, day, title))

            conn.commit()
        return redirect(url_for('calendar_view', year=year))

    # Build calendar data for each month
    all_months = []
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        weeks = calendar.monthcalendar(year, month)
        events = get_user_events(user_id, year, month)

        month_data = {
            'name': month_name,
            'number': month,
            'weeks': weeks,
            'events': events,
        }
        all_months.append(month_data)

    return render_template('calendar.html', year=year, months=all_months)

# --- MAIN ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
