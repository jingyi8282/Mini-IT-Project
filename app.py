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
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if not name or not email or not password:
            return render_template("register.html", error="All fields required")

        if password != confirm:
            return render_template("register.html", error="Passwords do not match")

        if len(password) < 6:
            return render_template("register.html", error="Password too short (min 6 characters)")

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


@app.route("/tasks")
def tasks():
    if "email" not in session:
        return redirect(url_for("login"))

    user_tasks = db.get_tasks(session["email"])
    return render_template("tasks.html", name=session["name"], tasks=user_tasks)


@app.route("/add", methods=["POST"])
def add_task():
    if "email" not in session:
        return redirect(url_for("login"))

    title = request.form.get("tasks")
    priority = request.form.get("priority")
    deadline = request.form.get("deadline")

    if title:
        db.add_task(session["email"], tasks, priority, deadline)

    return redirect(url_for("tasks"))


@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    if "email" in session:
        db.delete_task(session["email"], task_id)
    return redirect(url_for("tasks"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if "email" not in session:
        return redirect(url_for("login"))

    tasks = db.get_tasks(session["email"])
    current_task = None
    for task in tasks:
        if task["id"] == task_id:
            current_task = task
            break

    if not current_task:
        return "Task not found"

    if request.method == "POST":
        new_title = request.form.get("tasks")
        new_priority = request.form.get("priority")
        new_deadline = request.form.get("deadline")
        db.update_task(session["email"], task_id, new_title, new_priority, new_deadline)
        return redirect(url_for("tasks"))

    return render_template("edit.html", task=current_task)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)