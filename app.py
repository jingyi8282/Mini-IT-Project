from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello from our Mini IT Project!'

@app.route('/login')
def login():
    return 'Login page - coming soon'

@app.route('/logout')
def logout():
    return 'Logout page - coming soon'

if __name__ == '__main__':
    app.run(debug=True)