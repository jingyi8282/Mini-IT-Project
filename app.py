from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template ('/home.html')


@app.route('/login')
def login():
    return 'Login page - coming soon'

@app.route('/logout')
def logout():
    return 'Logout page - coming soon'

if __name__ == 'main':
    app.run(debug=True)