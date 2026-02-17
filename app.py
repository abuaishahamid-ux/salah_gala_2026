
from flask import Flask, render_template, request, redirect, session
import sqlite3, uuid, os, qrcode
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

app = Flask(__name__)
app.secret_key = "salah_2026_secret"

# PLACEHOLDERS: replace with your real info after deploy
PAYSTACK_SECRET_KEY = "sk_test_c57ebe47de429f9c0064c21c1594628757a53784"
WHATSAPP_NUMBER = "233551153989"
CURRENT_SEASON = "2026"

# Ensure folders exist
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/gallery", exist_ok=True)

# Ensure DB exists
if not os.path.exists("database.db"):
    open("database.db", "a").close()

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            manager TEXT,
            coach TEXT,
            payment_status TEXT,
            reference TEXT,
            season TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            team_name TEXT,
            position TEXT,
            photo TEXT,
            season TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register_team", methods=["GET","POST"])
def register_team():
    if request.method == "POST":
        team_name = request.form["team_name"]
        manager = request.form["manager"]
        coach = request.form["coach"]
        reference = str(uuid.uuid4())
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO teams (team_name, manager, coach, payment_status, reference, season) VALUES (?, ?, ?, ?, ?, ?)",
                  (team_name, manager, coach, "Pending", reference, CURRENT_SEASON))
        conn.commit()
        conn.close()
        return redirect(f"https://wa.me/{WHATSAPP_NUMBER}?text=New Team Registered: {team_name} Season 2026")
    return render_template("register_team.html")

@app.route("/register_player", methods=["GET","POST"])
def register_player():
    if request.method == "POST":
        player_name = request.form["player_name"]
        team_name = request.form["team_name"]
        position = request.form["position"]
        photo = request.files["photo"]
        photo_path = os.path.join("static/uploads", photo.filename)
        photo.save(photo_path)

        qr = qrcode.make(f"{player_name} | {team_name} | 2026")
        qr_path = os.path.join("static/uploads", f"{player_name}_qr.png")
        qr.save(qr_path)

        pdf_path = os.path.join("static/uploads", f"{player_name}_card.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=(3.5*inch,2*inch))
        elements = []
        elements.append(Paragraph("<b>Salah Football Gala 2026</b>", ParagraphStyle('title', fontSize=10)))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(f"Name: {player_name}", ParagraphStyle('normal', fontSize=8)))
        elements.append(Paragraph(f"Team: {team_name}", ParagraphStyle('normal', fontSize=8)))
        elements.append(Paragraph(f"Position: {position}", ParagraphStyle('normal', fontSize=8)))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Image(photo_path, width=1*inch, height=1*inch))
        elements.append(Image(qr_path, width=0.8*inch, height=0.8*inch))
        doc.build(elements)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO players (player_name, team_name, position, photo, season) VALUES (?, ?, ?, ?, ?)",
                  (player_name, team_name, position, photo.filename, CURRENT_SEASON))
        conn.commit()
        conn.close()
        return redirect(f"https://wa.me/{WHATSAPP_NUMBER}?text=New Player Card Created: {player_name} - {team_name}")
    return render_template("register_player.html")

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "Salah2026":
            session["admin"] = True
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM teams WHERE season = ?", (CURRENT_SEASON,))
    teams = c.fetchall()
    c.execute("SELECT * FROM players WHERE season = ?", (CURRENT_SEASON,))
    players = c.fetchall()
    conn.close()
    return render_template("dashboard.html", teams=teams, players=players)

if __name__ == "__main__":
    app.run()
