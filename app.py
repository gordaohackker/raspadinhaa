from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devsecret")

DATABASE = os.path.join(os.path.dirname(__file__), "database.db")

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cur = db.cursor()
    # users table: email, password (plaintext for demo), credits
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            credits INTEGER DEFAULT 100
        )
    """)
    # settings for probabilities
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    # default loss probability 80%
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("loss_prob", "0.8"))
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def query_setting(key):
    db = get_db()
    cur = db.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    return row["value"] if row else None

def set_setting(key, value):
    db = get_db()
    db.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    db.commit()

# Admin credentials (should be changed in production)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "senha123")

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("play"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        db = get_db()
        try:
            db.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            db.commit()
            flash("Conta criada. Faça login.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email já cadastrado.")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("play"))
        flash("Credenciais inválidas.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/play", methods=["GET", "POST"])
def play():
    if "user_id" not in session:
        return redirect(url_for("login"))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    result = None
    cost = 5
    if request.method == "POST":
        if user["credits"] < cost:
            flash("Créditos insuficientes.")
        else:
            loss_prob = float(query_setting("loss_prob") or 0.8)
            win = random.random() > loss_prob
            if win:
                prize = random.choice([10, 20, 50, 100, 200, 500, 1000])
                user_new = user["credits"] + prize - cost
                result = f"Você ganhou R${prize}! (Custo: R${cost})"
            else:
                user_new = user["credits"] - cost
                result = f"Você perdeu R${cost}."
            db.execute("UPDATE users SET credits=? WHERE id=?", (user_new, user["id"]))
            db.commit()
            user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return render_template("play.html", user=user, result=result)

# Admin routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Credenciais de admin inválidas.")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapped

@app.route("/admin/dashboard", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    db = get_db()
    if request.method == "POST":
        loss_prob = float(request.form.get("loss_prob", "0.8"))
        if 0 <= loss_prob <= 1:
            set_setting("loss_prob", str(loss_prob))
            flash("Probabilidade de perda atualizada.")
    users = db.execute("SELECT * FROM users").fetchall()
    current_loss = query_setting("loss_prob")
    return render_template("admin_dashboard.html", users=users, loss_prob=current_loss)

@app.route("/admin/create_demo/<int:user_id>")
@admin_required
def create_demo(user_id):
    flash("Use registro normal para criar contas de demonstração.")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
