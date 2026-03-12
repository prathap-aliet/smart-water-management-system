from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import matplotlib
matplotlib.use('Agg')   # Fix for server (no GUI)
import matplotlib.pyplot as plt
import io

app = Flask(__name__)
app.secret_key = "smart_water_secret"

DATABASE = "water.db"

# -------------------------
# Database Connection
# -------------------------
def get_db():
    return sqlite3.connect(DATABASE)


# -------------------------
# Create Database Tables
# -------------------------
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level INTEGER,
            usage INTEGER,
            quality TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Default Users
    cursor.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1,'admin','admin')")
    cursor.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (2,'user1','1234')")
    cursor.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (3,'user2','abcd')")

    conn.commit()
    conn.close()

init_db()


# -------------------------
# Login
# -------------------------
@app.route('/', methods=['GET','POST'])
def login():
    error = None

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect('/dashboard')
        else:
            error = "Invalid Username or Password"

    return render_template("login.html", error=error)


# -------------------------
# Dashboard
# -------------------------
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM water_data")
    data = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        data=data,
        user=session['user']
    )


# -------------------------
# Add Water Data
# -------------------------
@app.route('/add', methods=['GET','POST'])
def add():

    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':

        level = request.form['level']
        usage = request.form['usage']
        quality = request.form['quality']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO water_data(level,usage,quality) VALUES(?,?,?)",
            (level,usage,quality)
        )

        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template("add_data.html")


# -------------------------
# Delete Data
# -------------------------
@app.route('/delete/<int:id>')
def delete(id):

    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM water_data WHERE id=?", (id,))
    conn.commit()

    conn.close()

    return redirect('/dashboard')


# -------------------------
# Water Usage Graph
# -------------------------
@app.route('/graph')
def graph():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, usage FROM water_data")
    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return "No data available to display graph."

    ids = [row[0] for row in rows]
    usage = [row[1] for row in rows]

    plt.figure(figsize=(9,5))
    plt.plot(ids, usage, color='#007bff', marker='o', linewidth=3)
    plt.fill_between(ids, usage, color='#66b3ff', alpha=0.4)

    plt.title("Smart Water Usage Analysis")
    plt.xlabel("Record ID")
    plt.ylabel("Water Usage (Litres)")
    plt.grid(True)

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    plt.close()

    return send_file(img, mimetype='image/png')


# -------------------------
# Logout
# -------------------------
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# -------------------------
# Run App
# -------------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
