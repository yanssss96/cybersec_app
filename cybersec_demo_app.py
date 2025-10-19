from flask import Flask, render_template, request, redirect, url_for, session
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cyberlab-secret-key"

LOG_FILE = os.path.join("logs", "connections.log")

# Base de données simulée
users = {
    "admin@cyberlab.com": "admin"
}

# --- Fonction de log ---
def log_event(event_type, email, status):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {event_type.upper()} | {email} | {status}\n")


# === PAGE D’ACCUEIL ===
@app.route('/')
def home():
    # Vérifie si l'utilisateur est connecté
    if 'user' not in session:
        return redirect(url_for('login'))

    # Récupère l'onglet actif (ex : ?tab=about)
    tab = request.args.get('tab', '')
    return render_template('home.html', tab=tab)


# === PAGE DE CONNEXION ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Vérifie les identifiants
        if email in users and users[email] == password:
            session['user'] = email
            log_event("login", email, "success")
            return redirect(url_for('home'))  # redirige vers home.html
        else:
            log_event("login", email or "unknown", "failed")
            error = "Identifiants incorrects. Réessaie."

    return render_template('login.html', error=error)


# === PAGE D’INSCRIPTION ===
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if not email or not password or not confirm:
            message = "Tous les champs sont obligatoires."
        elif password != confirm:
            message = "Les mots de passe ne correspondent pas."
        elif email in users:
            message = "Cet utilisateur existe déjà."
        else:
            users[email] = password
            log_event("register", email, "success")
            message = "Compte créé avec succès. Connectez-vous maintenant."
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


if __name__ == "__main__":
    app.run(debug=True)
