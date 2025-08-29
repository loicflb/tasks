from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret-key'  # À sécuriser !

DB_NAME = 'database.db'


def init_db():
    if not os.path.exists(DB_NAME):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    done INTEGER DEFAULT 0,
                    created_by TEXT
                )
            ''')
            # Utilisateur par défaut
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin'))
            conn.commit()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw))
            result = c.fetchone()
            if result:
                session['user'] = user
                return redirect('/dashboard')
            else:
                return "Login failed"
    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        desc = request.form['description']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO tasks (description, created_by) VALUES (?, ?)", (desc, session['user']))
            conn.commit()

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM tasks")
        tasks = c.fetchall()

    return render_template('dashboard.html', tasks=tasks, user=session['user'])


@app.route('/done/<int:task_id>')
def mark_done(task_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
        conn.commit()
    return redirect('/dashboard')

@app.route('/delete_done')
def delete_done():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE done = 1")
        conn.commit()
    return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)  # accessible sur le réseau local