from flask import Flask, render_template, request, redirect, url_for, session
from database import Database

app = Flask(__name__)
app.secret_key = "abc123"
db = Database()

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if not name or not email or not password:
            return render_template("register.html", error="All fields required")

        if password != confirm:
            return render_template("register.html", error="Passwords do not match")

        if db.create_user(name, email, password):
            return redirect(url_for("login"))
        else:
            return render_template("register.html", error="Email already exists")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.check_login(email, password)
        if user:
            session["email"] = user[0]
            session["name"] = user[1]
            return redirect(url_for("tasks"))
        else:
            return render_template("login.html", error="Wrong email or password")

    return render_template("login.html")

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email")
        new_password = request.form.get("new_password")
        confirm = request.form.get("confirm_password")

        if new_password != confirm:
            return render_template("forgot.html", error="Passwords do not match")
        
        if email in db.users:
            db.users[email]["password"] = new_password
            db.save_users()
            return redirect(url_for("login"))
        else:
            return render_template("forgot.html", error="Email not found")
            
    return render_template("forgot.html")

@app.route("/tasks")
def tasks():
    if "email" not in session:
        return redirect(url_for("login"))

    user_tasks = db.get_tasks(session["email"])
    
    display_tasks = []
    for t in user_tasks:
        days_rem = 0 
        display_tasks.append([
            t.get('title', ''),      
            t.get('priority', ''),   
            t.get('deadline', ''),   
            days_rem,        
            t.get('id', 0)          
        ])
    
    return render_template("tasks.html", name=session.get("name"), tasks=display_tasks)

@app.route("/add", methods=["POST"])
def add_task():
    if "email" not in session:
        return redirect(url_for("login"))

    title = request.form.get("tasks")
    priority = request.form.get("priority")
    deadline = request.form.get("deadline")

    if title:
        db.add_task(session["email"], title, priority, deadline)

    return redirect(url_for("tasks"))

@app.route("/delete/<int:task_id>", methods=["GET", "POST"])
def delete_task(task_id):
    if "email" in session:
        db.delete_task(session["email"], task_id)
    return redirect(url_for("tasks"))

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if "email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_title = request.form.get("tasks")
        new_priority = request.form.get("priority")
        new_deadline = request.form.get("deadline")
        db.update_task(session["email"], task_id, new_title, new_priority, new_deadline)
        return redirect(url_for("tasks"))

    user_tasks = db.get_tasks(session["email"])
    target = next((t for t in user_tasks if t["id"] == task_id), None)

    if not target:
        return "Task not found"

    task_list = [
        target.get('title', ''), 
        target.get('priority', ''), 
        target.get('deadline', '')
    ]
    return render_template("edit.html", task=task_list, task_id=task_id)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)