import os
import sqlite3
import requests
import qrcode
from flask import Flask, render_template, request, redirect, session, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "database.db"
PAYSTACK_SECRET_KEY = "sk_test_c57ebe47de429f9c0064c21c1594628757a53784"
PAYSTACK_PUBLIC_KEY = "pk_test_2b16d364e909e41239dbe9963e849d596a5cbbee"

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    team TEXT,
                    position TEXT,
                    pin TEXT UNIQUE,
                    paid INTEGER DEFAULT 0
                )''')
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        team = request.form["team"]
        position = request.form["position"]
        pin = request.form["pin"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, team, position, pin) VALUES (?, ?, ?, ?)",
                      (name, team, position, pin))
            conn.commit()
        except:
            flash("PIN already exists!")
            return redirect("/register")
        conn.close()
        return redirect("/pay/" + pin)
    return render_template("register.html")

@app.route("/pay/<pin>")
def pay(pin):
    return render_template("pay.html", pin=pin, public_key=PAYSTACK_PUBLIC_KEY)

@app.route("/verify")
def verify():
    reference = request.args.get("reference")
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    response = requests.get(url, headers=headers).json()

    if response.get("data") and response["data"]["status"] == "success":
        pin = response["data"]["metadata"]["pin"]
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("UPDATE users SET paid=1 WHERE pin=?", (pin,))
        conn.commit()
        conn.close()
        flash("Payment successful! You can login.")
        return redirect("/login")

    flash("Payment verification failed.")
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pin = request.form["pin"]
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE pin=? AND paid=1", (pin,))
        user = c.fetchone()
        conn.close()
        if user:
            session["pin"] = pin
            return redirect("/dashboard")
        flash("Invalid PIN or payment incomplete.")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "pin" not in session:
        return redirect("/login")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, name, team, position FROM users WHERE pin=?", (session["pin"],))
    user = c.fetchone()
    conn.close()
    return render_template("dashboard.html", user=user)

@app.route("/generate_card")
def generate_card():
    if "pin" not in session:
        return redirect("/login")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, name, team, position FROM users WHERE pin=?", (session["pin"],))
    user = c.fetchone()
    conn.close()

    qr = qrcode.make(f"PlayerID:{user[0]} Name:{user[1]} Team:{user[2]}")
    qr_path = f"static/cards/qr_{user[0]}.png"
    qr.save(qr_path)

    return render_template("card.html", user=user, qr_path=qr_path)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
