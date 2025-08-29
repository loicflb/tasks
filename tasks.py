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
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    assigned_to TEXT,
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


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user' not in session:
        return redirect('/')

    filter_category = request.args.get('filter', '')

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Récupérer les utilisateurs pour la sélection "assigned_to"
        c.execute("SELECT username FROM users")
        users = [row[0] for row in c.fetchall()]

        # Récupérer les tâches, filtrées si besoin
        if filter_category:
            c.execute("SELECT * FROM tasks WHERE category=?", (filter_category,))
        else:
            c.execute("SELECT * FROM tasks")
        tasks = c.fetchall()

    # Préparer les tâches dans un format dict (plus clair dans le template)
    tasks_list = []
    for t in tasks:
        tasks_list.append({
            'id': t[0],
            'title': t[1],
            'description': t[2],
            'category': t[3],
            'assigned_to': t[4],
            'done': t[5],
            'created_by': t[6]
        })

    return render_template('dashboard.html', tasks=tasks_list, user=session['user'], users=users, filter=filter_category)



@app.route('/done/<int:task_id>')
def mark_done(task_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
        conn.commit()
    return redirect('/dashboard')

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user' not in session:
        return redirect('/')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
    return redirect('/dashboard')



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/add', methods=['POST'])
def add_task():
    if 'user' not in session:
        return redirect('/')

    title = request.form['title']
    description = request.form['description']
    category = request.form.get('category') or ''
    assigned_to = request.form.get('assigned_to') or ''
    created_by = session['user']

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO tasks (title, description, category, assigned_to, created_by) VALUES (?, ?, ?, ?, ?)",
            (title, description, category, assigned_to, created_by)
        )
        conn.commit()

    return redirect('/dashboard')



if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)  # accessible sur le réseau local