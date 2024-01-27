from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from hashlib import sha256
import uuid
import os

app = Flask(__name__)

env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(f'config.{env.capitalize()}Config')

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and sha256(password.encode("utf-8")).hexdigest() == user.password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('/auth/login.html', error='Invalid username or password')
    return render_template('auth/login.html')

#logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            hashed_password = sha256(password.encode("utf-8")).hexdigest()
            new_user = User(id=uuid.uuid4().hex, username=username, password=hashed_password, email=email)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            return render_template('auth/register.html', error='Passwords do not match')
    return render_template('auth/register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('Stats/dashboard.html', username=session['username'])
    return redirect(url_for('login'))
@app.route('/analytics')
def analytics():
    if 'username' in session:
        return render_template('Stats/analytics.html', username=session['username'])
    return redirect(url_for('login'))
@app.route('/profile')
def profile():
    if 'username' in session:
        return render_template('Stats/profile.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/youtube')
def youtube():
    if 'username' in session:
        return render_template('Stats/youtube.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/twitter')
def twitter():
    if 'username' in session:
        return render_template('Stats/twitter.html', username=session['username'])
    return redirect(url_for('login'))
@app.route('/ticket')
def ticket():
    if 'username' in session:
        return render_template('Stats/tickets.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/instagram')
def instagram():
    if 'username' in session:
        return render_template('Stats/instagram.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/about')
def about():
    if 'username' in session:
        return render_template('Stats/about.html', username=session['username'])
    return redirect(url_for('login'))
@app.route('/settings')
def settings():
    if 'username' in session:
        return render_template('Stats/settings.html', username=session['username'])
    return redirect(url_for('login'))
@app.route('/contact')
def contact():
    if 'username' in session:
        return render_template('Stats/contact.html', username=session['username'])
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

