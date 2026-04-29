from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from database import Database

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


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = db.check_login(email, password)
        
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]
            return redirect(url_for('tasks'))
        else:
            return render_template('login.html', error="Wrong email or password!")
    
    return render_template('login.html')


# LOGOUT
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
    return render_template("tasks.html", tasks=user_tasks)


# ADD TASK
@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == "POST":
        title = request.form['title']
        priority = request.form.get('priority', 'Medium')
        deadline = request.form.get('deadline', '')
        category = request.form.get('category', 'Subjects')
        
        db.add_task(session['user_id'], title, priority, deadline, category)
        return redirect('/tasks')


# COMPLETE TASK 
@app.route('/complete/<int:task_id>')
def complete(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db.update_task_status(task_id, session['user_id'], 1)
    return redirect('/tasks')


# DELETE TASK 
@app.route('/delete/<int:task_id>')
def delete(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db.delete_task(task_id, session['user_id'])
    return redirect('/tasks')


if __name__ == '__main__':
    app.run(debug=True)