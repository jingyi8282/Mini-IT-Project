from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from database import Database

app = Flask(__name__)

db = Database()


@app.route('/')
def home():
    return render_template('home.html')


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if not name or not email or not password:
            return render_template('register.html', error="All fields are required!")

        if "@" not in email or "." not in email:
            return render_template('register.html', error="Invalid email address!")

        if password != confirm:
            return render_template('register.html', error="Passwords do not match!")

        if len(password) < 6:
            return render_template('register.html', error="Password must be at least 6 characters long!")

        hashed_password = generate_password_hash(password)

        result = db.create_user(name, email, hashed_password)

        if result:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error="Email already exists.")

    return render_template('register.html')


# LOGIN (simple for now)
@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def logout():
    return 'Logout page - coming soon'

@app.route('/tasks')
def tasks():
    return 'Hi'

if __name__ == '__main__':
    app.run(debug=True)