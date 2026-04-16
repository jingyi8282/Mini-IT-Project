from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from database import Database

app = Flask(__name__)
app.secret_key = 'mysecretkey123'

db = Database()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']

        # Validation
        if not name or not email or not password:
            return render_template('register.html', error="All fields are required!")

        # email format check (invalid email)
        if "@" not in email or "." not in email:
            return render_template('register.html', error="Invalid email address!")

        # password match
        if password != confirm:
            return render_template('register.html', error="Passwords do not match!")

        # password rule
        if len(password) < 6:
            return render_template('register.html', error="Password must be at least 6 characters long!")

        # Hash password
        hashed_password = generate_password_hash(password)

        result = db.create_user(name, email, hashed_password)

        # email already exists 
        if result == True:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error="Email already exists. Please use another email.")

    return render_template('register.html')


@app.route('/')
def home():
    return redirect(url_for('register'))


# simple login (since you redirect to it)
@app.route('/login', methods=['GET', 'POST'])
def login():
    return "Login page (will be built soon)"


if __name__ == 'main':
    app.run(debug=True)