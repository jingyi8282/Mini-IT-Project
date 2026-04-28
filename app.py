from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from database import Database
from datetime import datetime

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

tasks_list =[]
@app.route('/tasks')
def tasks():
    return render_template ("tasks.html", tasks=tasks_list)

@app.route('/add', methods=['POST','GET'])
def add_task():
    if request.method == "POST":
        tasks = request.form['tasks']
        priority = request.form['priority']
        deadline = request.form['deadline']
        today =datetime.now().date()
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        due_date = deadline_date.strftime('%d-%m-%Y')
        remaining_days = (deadline_date - today ).days
        tasks_list.append([tasks, priority, due_date, remaining_days])
        return redirect('/tasks')
    
@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 0 <= task_id < len(tasks_list):
        tasks_list.pop(task_id)
    return redirect('/tasks')

@app.route('/edit/<int:task_id>', methods=['GET','POST'])
def edit_task(task_id):
    if task_id < 0 or task_id>=len(tasks_list):
        return redirect ('/tasks')
    if request.method =="POST" :
        new_task_name = request.form('tasks')
        new_date = request.form('deadline')
        tasks_list[task_id][0] = new_task_name
        tasks_list[task_id][4] = new_date
        
        return redirect ('/tasks')
    task = tasks_list[task_id]
    return render_template('edit.html', task=task, task_id=task_id)

        
     



if __name__ == '__main__':
    app.run(debug=True)