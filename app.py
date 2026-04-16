from flask import Flask, render_template, request ,redirect

app = Flask(__name__)

@app.route('/')
def home():
    return render_template ('home.html')


@app.route('/login')
def login():
    return 'Login page - coming soon'

@app.route('/logout')
def logout():
    return 'Logout page - coming soon'

tasks_list = []
@app.route('/tasks')
def tasks():
    return render_template("tasks.html",tasks=tasks_list)

@app.route('/add', methods=['POST','GET'])
def add():
    if request.method =='POST':
        tasks = request.form['tasks']
        tasks_list.append(tasks)
        return redirect('/tasks')
    


if __name__ == '__main__':
    app.run(debug=True)