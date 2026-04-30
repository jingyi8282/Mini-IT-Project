from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'mysecretkey123'

db = Database()

@app.route('/')
def home():
    return render_template('home.html')

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if not name or not email or not password:
            return render_template('register.html', error="All fields are required!")

        if "@" not in email or "." not in email:
            return render_template('register.html', error="Invalid email address!")

        if password != confirm:
            return render_template('register.html', error="Passwords do not match!")

        if len(password) < 6:
            return render_template('register.html', error="Minimum 6 characters required!")


        result = db.create_user(name, email, password)

        if result:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error="Email already exists.")

    return render_template('register.html')

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.check_login(email, password)
        
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]
            return redirect(url_for('tasks'))
        else:
            return render_template('login.html', error="Wrong email or password!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# TASKS
@app.route('/tasks')
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_tasks = db.get_user_tasks(session['user_id'])
    tasks_list = []
    
    for task in user_tasks:
        task_id = task[0]
        title = task[2]
        priority = task[3]
        deadline = task[4]
        
        due_date = "No deadline"
        remaining_days = 0
        
        if deadline:
            try:
                today = datetime.now().date()
                deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
                due_date = deadline_date.strftime('%d-%m-%Y')
                remaining_days = (deadline_date - today).days
            except:
                due_date = deadline

        tasks_list.append([title, priority, due_date, remaining_days, task_id])
    
    return render_template("tasks.html", tasks=tasks_list, name=session['user_name'])

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    title = request.form.get('tasks')
    priority = request.form.get('priority')
    deadline = request.form.get('deadline')
    
    db.add_task(session['user_id'], title, priority, deadline, "Subjects")
    return redirect(url_for('tasks'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db.delete_task(task_id, session['user_id'])
    return redirect(url_for('tasks'))
@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == "POST":
        title = request.form.get('tasks')
        priority = request.form.get('priority')
        deadline = request.form.get('deadline')
        db.update_task(task_id, session['user_id'], title, priority, deadline)
        return redirect(url_for('tasks'))
    
    user_tasks = db.get_user_tasks(session['user_id'])
    task_to_edit = None
    for t in user_tasks:
        if t[0] == task_id:
            task_to_edit = [t[2], t[3], t[4], 0, t[0]]
            break
    
    if task_to_edit:
        return render_template('edit.html', task=task_to_edit, task_id=task_id)
    return redirect(url_for('tasks'))

if __name__ == 'main':
    app.run(debug=True)