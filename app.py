from groq import Groq
from flask import Flask, render_template, request, redirect, url_for, session
from database import Database
from datetime import datetime
import PyPDF2  
import docx  
import os
import random
from werkzeug.utils import secure_filename
import glob

app = Flask(__name__)
app.secret_key = "abc123"
db = Database()

# ai notes feature
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

def call_groq_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}. Check your API key."

def calculate_days_remaining(deadline_str):
    if not deadline_str:
        return 0
    try:
        today = datetime.now().date()
        deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        remaining = (deadline_date - today).days
        return max(0, remaining)
    except ValueError:
        return 0
    
# ROUTES 
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/focus", methods=["GET", "POST"])
def focus_room():
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
            except Exception as e:
                return render_template("focus.html", error=f"File Error: {str(e)}")
        
        if not user_text:
            return render_template("focus.html", error="Please enter text or upload a file!")

        if action == "summarize":
            prompt = f"Summarize this content into 5 key bullet points:\n\n{user_text}"
        elif action == "quiz":
            prompt = f"Create 5 multiple choice questions based on this:\n\n{user_text}"
        else:
            prompt = f"Analyze these notes:\n\n{user_text}"
        
        ai_output = call_groq_ai(prompt)

    quotes = [
        {
            "text" : "Success is no accident. It is hard work, perseverance, learning, studying, sacrifice and most of all, love of what you are doing or learning to do.",
            "author" : "Pelé, Brazilian football legend"
        },
        {
            "text" : "An investment in knowledge pays the best interest.",
            "author" : "Benjamin Franklin, writer and polymath"
        },
        {
            "text" : "Striving for success without hard work is like trying to harvest where you haven't plated.",
            "author" : "David Bly"
        },
        {
            "text" : "Success isn’t overnight. It’s when every day you get a little better than the day before. It all adds up.",
            "author" : "Dwayne Johnson"
        },
        {
            "text" : "Nothing is impossible. The word itself says 'I'm Possible.",
            "author" : "Audrey Hepburn"
        }
    ]
    
    random_quote = random.choice(quotes)
    return render_template("focus.html", result=ai_output, quotes=random_quote)

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
            db.update_streak(email)
            return redirect(url_for("dashboard"))
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

@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", name=session.get("name"))

@app.route("/tasks")
def tasks():
    if "email" not in session:
        return redirect(url_for("login"))
    user_tasks = db.get_tasks(session["email"])
    my_tasks, in_progress, completed = [], [], []
    for task in user_tasks:
        task_status = task.get("status", "my_task")
        deadline = task.get("deadline", "")
        days_left = calculate_days_remaining(deadline)
        
        task_data = [
            task.get("title", ""), task.get("priority", ""), 
            deadline, days_left, task.get("id", 0), 
            task.get("category", ""), task_status
        ]
        
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
        db.update_status(session["email"], task_id, new_status)
        if new_status == "completed":
            db.add_points(session["email"], 10)
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
    
    days_left = calculate_days_remaining(target.get('deadline', ''))
    task_list = [
        target.get('title', ''), target.get('priority', ''), 
        target.get('deadline', ''), days_left, target.get('id', 0), 
        target.get('category', ''), target.get('status', 'my_task')
    ]
    return render_template("edit.html", task=task_list, task_id=task_id)

@app.route("/profile")
def profile():
    if "email" not in session:
        return redirect(url_for("login"))
    
    user = db.users.get(session["email"], {})
    tasks = db.get_tasks(session["email"])
    
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
    points = db.get_points(session["email"])
    streak = db.get_streak(session["email"])
    bio = db.get_bio(session["email"])
    
    return render_template("profile.html",
                         name=session.get("name"),
                         email=session["email"],
                         joined_date=user.get("joined", "2025"),
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         points=points,
                         streak=streak,
                         profile_pic=user.get("pic"),
                         bio=bio)

@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    if "email" not in session:
        return redirect(url_for("login"))
    
    if "profile_photo" not in request.files:
        return redirect(url_for("profile"))
    
    file = request.files["profile_photo"]
    
    if file and file.filename:
        filename = secure_filename(f"{session['email']}_{file.filename}")
        file.save(os.path.join("static/uploads", filename))
        db.update_pic(session["email"], filename)
        return render_template("profile.html", success="Profile picture updated!")
    
    return render_template("profile.html", error="Invalid file type. Use PNG, JPG, or GIF.")

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "email" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        new_name = request.form.get("name")
        new_bio = request.form.get("bio")
        
        if new_name:
            db.users[session["email"]]["name"] = new_name
            session["name"] = new_name
            db.save_users()
        
        if new_bio is not None:
            db.update_bio(session["email"], new_bio)
        
        return redirect(url_for("profile"))
    
    user = db.users.get(session["email"], {})
    return render_template("edit_profile.html", 
                         name=session.get("name"),
                         bio=user.get("bio", ""))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "email" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        user = db.check_login(session["email"], current_password)
        if not user:
            return render_template("change_password.html", error="Current password is wrong!")
        
        if new_password != confirm_password:
            return render_template("change_password.html", error="New passwords do not match!")
        
        if len(new_password) < 6:
            return render_template("change_password.html", error="Password too short (min 6 chars)")
        
        db.reset_password(session["email"], new_password)
        return render_template("change_password.html", success="Password changed successfully!")
    
    return render_template("change_password.html")

@app.route("/delete_account", methods=["POST"])
def delete_account():
    if "email" not in session:
        return redirect(url_for("login"))
    
    email = session["email"]
    
    if email in db.users:
        del db.users[email]
        db.save_users()
    
    if email in db.tasks:
        del db.tasks[email]
        db.save_tasks()
    
    pic_path = os.path.join("static/uploads", f"{email}_*")
    for f in glob.glob(pic_path):
        os.remove(f)
    
    session.clear()
    return render_template("login.html", error="Account permanently deleted.")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)