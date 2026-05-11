import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, session
from database import Database

app = Flask(__name__)
app.secret_key = "abc123"
db = Database()

genai.configure(api_key="AIzaSyDJcu3TkPCDW9KaCvdQnWlDLxlvrUyla8k")
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/focus")
def focus_room():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("focus.html")

# register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Pulls 'username' to match the name attribute in your register.html
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

# login
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

# forgot pw
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
            db.save_data()
            return redirect(url_for("login"))
        else:
            return render_template("forgot.html", error="Email not found")
            
    return render_template("forgot.html")

# quick notes
@app.route("/notes", methods=["GET", "POST"])
def notes():
    if "email" not in session:
        return redirect(url_for("login"))
    
    ai_output = ""
    if request.method == "POST":
        user_text = request.form.get("content")
        action = request.form.get("action")
        
        if not user_text:
            return render_template("notes.html", error="Please paste some notes first!")

        if action == "summarize":
            prompt = f"Summarize these study notes into clear bullet points: {user_text}"
        elif action == "quiz":
            prompt = f"Create 3 multiple choice questions based on these notes. List answers at the end: {user_text}"
        
        try:
            response = model.generate_content(prompt)
            ai_output = response.text
        except Exception as e:
            ai_output = "AI Error. Check your API key and connection."

    return render_template("notes.html", result=ai_output)

# tasks
@app.route("/tasks")
def tasks():
    if "email" not in session:
        return redirect(url_for("login"))

    user_tasks = db.get_tasks(session["email"])
    display_tasks = []
    for t in user_tasks:
        display_tasks.append([
            t.get('title', ''),      
            t.get('priority', ''),   
            t.get('deadline', ''),   
            0, # Days remaining logic can be added here
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

    task_list = [target.get('title', ''), target.get('priority', ''), target.get('deadline', '')]
    return render_template("edit.html", task=task_list, task_id=task_id)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)