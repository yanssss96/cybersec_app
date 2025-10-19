from flask import Flask, render_template, request, redirect, url_for, session
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# --- Application Flask ---
app = Flask(__name__)
# Utilise une variable d'environnement si disponible, sinon fallback (changer en production)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cyberlab-secret-key")

# --- Configuration Base de données SQLite ---
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "users.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Table Users ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Crée la base si elle n'existe pas
with app.app_context():
    db.create_all()
    # Crée un utilisateur admin par défaut pour tests si absent (email: admin@cyberlab.com / mot de passe: admin)
    if not User.query.filter_by(email="admin@cyberlab.com").first():
        hashed = generate_password_hash("admin")
        admin = User(email="admin@cyberlab.com", password=hashed)
        db.session.add(admin)
        db.session.commit()

# --- Fichier de logs ---
LOG_FILE = os.path.join(basedir, "logs", "connections.log")
def log_event(event_type, email, status):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {event_type.upper()} | {email} | {status}\n")

# === PAGE D’ACCUEIL ===
@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    tab = request.args.get('tab', '')
    return render_template('home.html', tab=tab, user=session.get('user'))

# === PAGE DE CONNEXION ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user'] = email
            log_event("login", email, "success")
            return redirect(url_for('home'))
        else:
            log_event("login", email or "unknown", "failed")
            error = "Identifiants incorrects. Réessaie."
    return render_template('login.html', error=error)

# === PAGE D’INSCRIPTION ===
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not email or not password or not confirm:
            message = "Tous les champs sont obligatoires."
        elif password != confirm:
            message = "Les mots de passe ne correspondent pas."
        elif User.query.filter_by(email=email).first():
            message = "Cet utilisateur existe déjà."
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(email=email, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            log_event("register", email, "success")
            return redirect(url_for('login'))
    return render_template('register.html', message=message)

# === DÉCONNEXION ===
@app.route('/logout')
def logout():
    email = session.get('user')
    if email:
        log_event("logout", email, "success")
    session.pop('user', None)
    return redirect(url_for('login'))

# === Lancer l’application sur Render ou local ===
if __name__ == "__main__":
    # Utilise le port fourni par Render (ou 5000 en local)
    port = int(os.environ.get("PORT", 5000))
    # Ne pas activer debug=True en production
    app.run(host="0.0.0.0", port=port)
