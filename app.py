from flask import Flask, render_template, request, redirect, url_for, session
from database import Database
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
db = Database()

@app.route('/')
def home():
    return render_template('home.html')

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, email, password = request.form.get('name'), request.form.get('email'), request.form.get('password')
        if db.create_user(name, email, password):
            return redirect(url_for('login'))
        return render_template('register.html', error="User exists!")
    return render_template('register.html')

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = db.check_login(request.form.get('email'), request.form.get('password'))
        if user:
            session['user_id'], session['user_name'] = user[0], user[1]
            return redirect(url_for('tasks'))
        return render_template('login.html', error="Login failed!")
    return render_template('login.html')

# TASKS
@app.route('/tasks')
def tasks():
    if 'user_id' not in session: return redirect(url_for('login'))
    raw = db.get_user_tasks(session['user_id'])
    processed = []
    for t in raw:
        try:
            d_date = datetime.strptime(t[4], '%Y-%m-%d').date()
            rem = (d_date - datetime.now().date()).days
            due = d_date.strftime('%d-%m-%Y')
        except:
            rem, due = 0, t[4]
        processed.append([t[2], t[3], due, rem, t[0]])
    return render_template("tasks.html", tasks=processed, user_name=session['user_name'])

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' in session:
        db.add_task(session['user_id'], request.form.get('tasks'), request.form.get('priority'), request.form.get('deadline'), "General")
    return redirect(url_for('tasks'))

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        db.update_task(task_id, session['user_id'], request.form.get('tasks'), request.form.get('priority'), request.form.get('deadline'))
        return redirect(url_for('tasks'))
    all_t = db.get_user_tasks(session['user_id'])
    task = next((x for x in all_t if x[0] == task_id), None)
    if task:
        return render_template('edit.html', task=[task[2], task[3], task[4], 0, task[0]], task_id=task_id)
    return redirect(url_for('tasks'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' in session: db.delete_task(task_id, session['user_id'])
    return redirect(url_for('tasks'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)