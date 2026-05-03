from flask import Flask, render_template, request, redirect, url_for, session
from database import Database
from datetime import datetime

app = Flask(__name__)
app.secret_key = "abc123"
db = Database()


@app.route("/")
def home():
    return render_template("home.html")


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
        if len(password) < 6:
            return render_template("register.html", error="Password too short (min 6 chars)")

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

        if not email or not new_password:
            return render_template("forgot.html", error="Email and password required")
        if new_password != confirm:
            return render_template("forgot.html", error="Passwords do not match")
        if len(new_password) < 6:
            return render_template("forgot.html", error="Password too short (min 6 chars)")

        if db.reset_password(email, new_password):
            return render_template("login.html", error="Password reset! Please login.")
        else:
            return render_template("forgot.html", error="Email not found")

    return render_template("forgot.html")


@app.route("/tasks")
def tasks():
    if "email" not in session:
        return redirect(url_for("login"))

    user_tasks = db.get_tasks(session["email"])
    
    my_tasks = []
    in_progress = []
    completed = []
    
    for task in user_tasks:
        task_status = task.get("status", "my_task")
        
        days_remaining = 0
        due_display = task.get("deadline", "")
        if task.get("deadline"):
            try:
                today = datetime.now().date()
                deadline_date = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
                days_remaining = (deadline_date - today).days
                due_display = deadline_date.strftime("%d-%m-%Y")
            except:
                due_display = task["deadline"]
        
        task_data = [
            task.get("title", ""),
            task.get("priority", ""),
            due_display,
            days_remaining,
            task.get("id", 0),
            task.get("category", ""),
            task_status
        ]
        
        if task_status == "my_task":
            my_tasks.append(task_data)
        elif task_status == "in_progress":
            in_progress.append(task_data)
        elif task_status == "completed":
            completed.append(task_data)
        else:
            my_tasks.append(task_data)
    
    return render_template("tasks.html", 
                         name=session.get("name"),
                         my_tasks=my_tasks,
                         in_progress=in_progress,
                         completed=completed)


@app.route("/add", methods=["POST"])
def add_task():
    if "email" not in session:
        return redirect(url_for("login"))
    
    title = request.form.get("tasks")
    priority = request.form.get("priority")
    deadline = request.form.get("deadline")
    category = request.form.get("category")
    
    if title and priority:
        db.add_task(session["email"], title, priority, deadline, category)
    return redirect(url_for("tasks"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if "email" in session:
        db.delete_task(session["email"], task_id)
    return redirect(url_for("tasks"))


@app.route("/move/<int:task_id>", methods=["POST"])
def move_task(task_id):
    if "email" in session:
        new_status = request.form.get("status")
        db.update_task_status(session["email"], task_id, new_status)
    return redirect(url_for("tasks"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if "email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_title = request.form.get("tasks")
        new_priority = request.form.get("priority")
        new_deadline = request.form.get("deadline")
        new_category = request.form.get("category")
        db.update_task(session["email"], task_id, new_title, new_priority, new_deadline, new_category)
        return redirect(url_for("tasks"))

    user_tasks = db.get_tasks(session["email"])
    target = None
    for t in user_tasks:
        if t["id"] == task_id:
            target = t
            break
    
    if not target:
        return "Task not found"

    task_list = [
        target.get('title', ''),
        target.get('priority', ''),
        target.get('deadline', ''),
        0,
        target.get('id', 0),
        target.get('category', ''),
        target.get('status', 'my_task')
    ]
    return render_template("edit.html", task=task_list, task_id=task_id)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)