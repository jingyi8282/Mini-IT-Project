from groq import Groq
from flask import Flask, render_template, request, redirect, url_for, session
from database import Database
from datetime import datetime
import PyPDF2  
<<<<<<< HEAD
import docx 
=======
import docx  # Added for Word document support
>>>>>>> auth
import os

app = Flask(__name__)
app.secret_key = "abc123"
db = Database()

<<<<<<< HEAD
GROQ_API_KEY = ""  
client = Groq(api_key=GROQ_API_KEY)

def call_groq_ai(prompt, max_tokens=1000):
    """Function to call Groq AI using the Llama 3.3 model"""
=======
GROQ_API_KEY = "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"  
client = Groq(api_key=GROQ_API_KEY)

def call_groq_ai(prompt, max_tokens=1000):
>>>>>>> auth
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": "You are a helpful study assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"
<<<<<<< HEAD

# authentication
=======
>>>>>>> auth

@app.route("/")
def home():
    return render_template("home.html")

<<<<<<< HEAD
@app.route('/focus')
def focus():
    return render_template('focus.html')
=======
@app.route("/focus")
def focus_room():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("focus.html")
>>>>>>> auth

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
        if not email or not new_password:
            return render_template("forgot.html", error="Email and password required")
        if new_password != confirm:
            return render_template("forgot.html", error="Passwords do not match")
        if db.reset_password(email, new_password):
            return render_template("login.html", error="Password reset! Please login.")
        else:
            return render_template("forgot.html", error="Email not found")
    return render_template("forgot.html")

<<<<<<< HEAD
# quick notes
=======
>>>>>>> auth
@app.route("/notes", methods=["GET", "POST"])
def notes():
    if "email" not in session:
        return redirect(url_for("login"))
    
    ai_output = ""
    if request.method == "POST":
        user_text = request.form.get("content")
        uploaded_file = request.files.get("pdf_file")
        action = request.form.get("action")
        
        if uploaded_file and uploaded_file.filename != '':
            file_ext = uploaded_file.filename.split('.')[-1].lower()
            try:
                if file_ext == 'pdf':
                    reader = PyPDF2.PdfReader(uploaded_file)
                    user_text = "".join([page.extract_text() for page in reader.pages])
                elif file_ext == 'docx':
                    doc = docx.Document(uploaded_file)
                    user_text = "\n".join([para.text for para in doc.paragraphs])
                else:
                    return render_template("notes.html", error="Unsupported file type.")
            except Exception as e:
                return render_template("notes.html", error=f"Error reading file: {str(e)}")
        
        if not user_text:
            return render_template("notes.html", error="Please paste notes or upload a file!")

        if len(user_text) > 8000:
            user_text = user_text[:8000]

        if action == "summarize":
<<<<<<< HEAD
            prompt = f"Summarize these notes into 3-5 clear bullet points:\n\n{user_text}"
        elif action == "quiz":
            prompt = f"Create 5 multiple choice questions based on these notes. Provide options and the correct answer for each:\n\n{user_text}"
        else:
            prompt = f"Analyze these notes and explain the key concepts:\n\n{user_text}"
=======
            prompt = f"Summarize these notes into 3-5 bullet points:\n\n{user_text}"
        elif action == "quiz":
            prompt = f"Create 5 multiple choice questions based on these notes:\n\n{user_text}"
        else:
            prompt = f"Analyze these notes:\n\n{user_text}"
>>>>>>> auth
        
        ai_output = call_groq_ai(prompt)

    return render_template("notes.html", result=ai_output)
<<<<<<< HEAD

# tasks
=======
>>>>>>> auth

@app.route("/tasks")
def tasks():
    if "email" not in session:
        return redirect(url_for("login"))
    user_tasks = db.get_tasks(session["email"])
    my_tasks, in_progress, completed = [], [], []
    for task in user_tasks:
        task_status = task.get("status", "my_task")
<<<<<<< HEAD
        task_data = [
            task.get("title", ""), task.get("priority", ""), 
            task.get("deadline", ""), 0, task.get("id", 0), 
            task.get("category", ""), task_status
        ]
=======
        task_data = [task.get("title", ""), task.get("priority", ""), task.get("deadline", ""), 0, task.get("id", 0), task.get("category", ""), task_status]
>>>>>>> auth
        if task_status == "in_progress":
            in_progress.append(task_data)
        elif task_status == "completed":
            completed.append(task_data)
        else:
            my_tasks.append(task_data)
    return render_template("tasks.html", name=session.get("name"), my_tasks=my_tasks, in_progress=in_progress, completed=completed)

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
    target = next((t for t in user_tasks if t["id"] == task_id), None)
    if not target: return "Task not found"
<<<<<<< HEAD
    task_list = [
        target.get('title', ''), target.get('priority', ''), 
        target.get('deadline', ''), 0, target.get('id', 0), 
        target.get('category', ''), target.get('status', 'my_task')
    ]
=======
    task_list = [target.get('title', ''), target.get('priority', ''), target.get('deadline', ''), 0, target.get('id', 0), target.get('category', ''), target.get('status', 'my_task')]
>>>>>>> auth
    return render_template("edit.html", task=task_list, task_id=task_id)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)