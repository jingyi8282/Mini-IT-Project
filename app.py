import os
from dotenv import load_dotenv
from groq import Groq
from flask import Flask, render_template, request, redirect, url_for, session
from database import Database
from datetime import datetime, timedelta
import PyPDF2  
import docx  
import random
import time
from werkzeug.utils import secure_filename
import glob
from collections import Counter
import plotly.graph_objects as go

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "abc123") # added inside our .env file instaed
db = Database()

# our api key inside .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# only initialize client if key exists
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        client = None
else:
    print("⚠️ GROQ_API_KEY not found in environment variables!")
    client = None


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
    
@app.context_processor
def inject_user_profile():
    profile_pic = None
    if "email" in session:
        user = db.users.get(session["email"], {})
        profile_pic = user.get("pic")
    return {"profile_pic": profile_pic, "user_image": bool(profile_pic)}


#admin routes

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        session.clear()

    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if db.check_admin_login(email, password):
            session.clear() 
            
            session["is_admin"] = True
            session["admin_email"] = email
            session["name"] = "Admin"
            
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("admin_login.html", error="Invalid admin credentials")
    
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    
    all_users = getattr(db, "users", {})
    all_tasks = getattr(db, "tasks", {})
    
    total_users = len(all_users)
    total_tasks = sum(len(tasks_list) for tasks_list in all_tasks.values())
  
    global_completed = 0
    global_overdue = 0
    today_str = datetime.today().strftime('%Y-%m-%d')

    for user_tasks in all_tasks.values():
        for t in user_tasks:
            status_clean = str(t.get('status', '')).lower()
            deadline = t.get('deadline')
            
            if status_clean in ['completed', 'complete']:
                global_completed += 1
            else:
                if deadline and deadline < today_str:
                    global_overdue += 1

    global_pending = max(0, total_tasks - global_completed)

    if total_tasks > 0:
        completion_percentage = round((global_completed / total_tasks) * 100)
        pending_percentage = 100 - completion_percentage
    else:
        completion_percentage = 0
        pending_percentage = 0

    admin_user_tracking = []
    for email, user_info in all_users.items():
        user_tasks_list = all_tasks.get(email, [])
        user_total = len(user_tasks_list)
        
        user_completed = sum(1 for t in user_tasks_list if str(t.get('status', '')).lower() in ['completed', 'complete'])
        
        if user_total > 0:
            user_percent = round((user_completed / user_total) * 100)
        else:
            user_percent = 0 
            
        profile_pic = user_info.get('pic') or 'default_profile.png'
        username = user_info.get('name') or 'Student'
        
        admin_user_tracking.append({
            'username': username,
            'email': email,
            'profile_pic': profile_pic,
            'completed_percent': user_percent,
            'pending_percent': 100 - user_percent if user_total > 0 else 0,
            'total_tasks': user_total
        })

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,total_tasks=total_tasks,total_overdue=global_overdue,global_completed=global_completed,global_pending=global_pending,
        completion_percentage=completion_percentage,pending_percentage=pending_percentage,user_tracking_list=admin_user_tracking)
    
@app.route("/admin/tasks")
def admin_tasks():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    filter_user = request.args.get("filter_user", "")
    
    all_tasks = db.get_all_users_tasks()
    
    if filter_user:
        all_tasks = [t for t in all_tasks if t["user_email"] == filter_user]
  
    all_users = []
    for email, user in db.users.items():
        all_users.append({
            "email": email,
            "name": user.get("name", email)
        })
    
    my_tasks_count = sum(1 for t in all_tasks if t.get("status") == "my_task")
    in_progress_count = sum(1 for t in all_tasks if t.get("status") == "in_progress")
    completed_count = sum(1 for t in all_tasks if t.get("status") == "completed")
    
    total = len(all_tasks)
    completion_rate = round((completed_count / total) * 100) if total > 0 else 0
    
    stats = {
        "my_tasks": my_tasks_count,
        "in_progress": in_progress_count,
        "completed": completed_count,
        "completion_rate": completion_rate
    }
    
    return render_template("admin_tasks.html",tasks=all_tasks,users=all_users,filter_user=filter_user,stats=stats)

#admin delete tasks
@app.route("/admin/delete_task/<int:task_id>", methods=["POST"])
def admin_delete_task(task_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    
    db.delete_any_task(task_id)
    return redirect(url_for("admin_tasks"))

#admin delete users
@app.route("/admin/delete_user/<string:email>", methods=["POST"])
def admin_delete_user(email):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    
    #admin cannot delete themselves
    if email == session.get("admin_email"):
        return redirect(url_for("manage_users"))
    
    db.delete_user_by_admin(email)
    return redirect(url_for("manage_users"))

#normal route
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
            prompt = f"""
You are a study assistant.

Summarize the following notes into short and easy-to-understand bullet points.

Rules:
- Keep the explanation simple for students
- Highlight important keywords
- Use bullet points
- Keep it concise but informative

Notes:
{user_text}
"""
        elif action == "quiz":
            prompt = f"""
You are a quiz generator for students.

Create 5 multiple choice questions based on the notes below.

Rules:
- Each question must have 4 options
- Show the correct answer
- Questions should be simple and educational
- Format clearly
- Explain the correct answer

Notes:
{user_text}
""" 
        else:
            prompt = f"Analyze these notes:\n\n{user_text}"
        
        ai_output = call_groq_ai(prompt)

    if session.get("timer_running") and "timer_end" in session:
        remaining = max(0, int(float(session.get("timer_end", 0)) - time.time()))
        if remaining == 0:
            session["timer_running"] = False
            session["timer_remaining"] = 0
        else:
            session["timer_remaining"] = remaining
    else:
        remaining = session.get("timer_remaining", 1500)

    minutes = remaining // 60
    seconds = remaining % 60
    time_string = f"{minutes:02d}:{seconds:02d}"

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


    return render_template("focus.html", result=ai_output, quotes=random_quote, timer_running=session.get("timer_running", False))

@app.route('/focus/timer/update')
def timer_update():
    if "timer_end" in session and session.get("timer_running"):
        end_time = float(session.get("timer_end", 0))
        remaining = max(0,round(end_time - time.time()))
        if remaining <= 0:
            session["timer_running"] = False
            session["timer_remaining"] = 0
            remaining = 0
        else:
            session["timer_remaining"] = remaining
    else:   
        remaining = session.get("timer_remaining", 1500)
    minutes = remaining // 60
    seconds = remaining % 60
    session.modified = True
    return f"{minutes:02d}:{seconds:02d}"

@app.route("/focus/timer/start")
def start_timer():
    if not session.get("timer_running", False):
        remaining = session.get("timer_remaining", 1500)
        session["timer_end"] = time.time() + float(remaining)
        session["timer_running"] = True
        session.modified = True
    return redirect(url_for("focus_room"))

@app.route("/focus/timer/pause")
def pause_timer():
    if session.get("timer_running", False) and "timer_end" in session:
        remaining = round(float(session.get("timer_end", 0)) - time.time())
        session["timer_remaining"] = max(0, remaining)
        session["timer_running"] = False
    return redirect(url_for("focus_room"))

@app.route("/focus/timer/reset/<mode>")
def reset_timer(mode):
    session["timer_running"] = False
    session.pop("timer_end", None)
    session["timer_mode"] = mode
    if mode == "work":
        session["timer_remaining"] = 1500
    else:
        session["timer_remaining"] = 300
    return redirect(url_for('focus_room'))

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
            # welcome notification
            db.add_notification(email, "Welcome!", "Thanks for joining Academic Diary! Start by adding your first task.", "success")
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
            
            # check their streak 
            streak = db.get_streak(email)
            if streak == 5:
                db.add_notification(email, "5 Day Streak! 🔥", "You've studied 5 days in a row! Amazing! Keep it up!", "success")
            elif streak == 10:
                db.add_notification(email, "10 Day Streak! 🏆", "10 days straight! You're on fire! Double digits!", "success")
            elif streak == 20:
                db.add_notification(email, "20 Day Streak! ⭐", "20 days! You're a study machine!", "success")
            elif streak == 30:
                db.add_notification(email, "30 Day Streak! 🎉", "30 days! One whole month! Incredible!", "success")
            elif streak == 50:
                db.add_notification(email, "50 Day Streak! 👑", "50 days! Legendary status unlocked!", "success")
            elif streak == 100:
                db.add_notification(email, "100 Day Streak! 🏅", "ONE HUNDRED DAYS! You're a study champion!", "success")
            
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
    
    user_email = session.get("email")

    all_user_tasks = db.get_tasks(user_email)

    current_filter = request.args.get('filter', 'category').lower().strip()

    completed_count = sum( 
        1 for task in all_user_tasks 
        if str(task.get('status', '')).lower() in ['completed', 'complete']
    )
    
    incomplete_count = sum(
        1 for task in all_user_tasks 
        if str(task.get('status', '')).lower() in ['my_task', 'my tasks', 'in_progress', 'in progress']
    )

    total_tasks = completed_count + incomplete_count

    today_str = datetime.today().strftime('%Y-%m-%d')
    overdue_count = 0
    
    # check for tasks due tomorrow 
    tomorrow_str = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    for task in all_user_tasks:
        status_clean = str(task.get('status', '')).lower()
        deadline = task.get('deadline') 
        
        # check overdue
        if status_clean not in ['completed', 'complete'] and deadline:
            if deadline < today_str:
                overdue_count += 1
        
        # check for tomorrow deadline
        if status_clean not in ['completed', 'complete'] and deadline == tomorrow_str:
            # check if already notified today
            already_notified = False
            notifs = db.get_notifications(user_email)
            for n in notifs:
                if "due tomorrow" in n.get("title", "").lower() and task.get("title") in n.get("message", ""):
                    already_notified = True
                    break
            if not already_notified:
                db.add_notification(user_email, "Task Due Tomorrow ⚠️", f"'{task.get('title')}' is due tomorrow! Don't forget!", "warning")

    
    donut_fig = go.Figure(data=[go.Pie(
        labels=['Incomplete', 'Complete'],values=[incomplete_count, completed_count],hole=0.75,marker=dict(colors=['#E2D6FF', '#8A4FFF']),
        textinfo='none',hoverinfo='label+value',sort=False)])
    
    donut_fig.update_layout(showlegend=True,legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=10, b=10, l=10, r=10),height=220,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=f'<b>{total_tasks}</b><br>total', x=0.5, y=0.5, font_size=14, showarrow=False, font_color='#1F2937')])
    
    donut_html = donut_fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    active_filter = request.args.get('filter', 'category')
    
    raw_data = []
    
    if active_filter == "category":
        raw_data = [t.get("category", "Uncategorized").strip() or "Uncategorized" for t in all_user_tasks]
    elif active_filter == "priority":
        raw_data = [t.get("priority", "Normal").strip() or "Normal" for t in all_user_tasks]
    elif active_filter == "deadline":
        raw_data = [t.get("deadline", "No Deadline").strip() or "No Deadline" for t in all_user_tasks]
    elif active_filter == "weekly":
        for t in all_user_tasks:
            date_str = t.get("deadline")
            if date_str:
                try:
                    task_date = datetime.strptime(date_str, "%Y-%m-%d")
                    raw_data.append(task_date.strftime("%A"))
                except ValueError:
                    raw_data.append("No Deadline")
            else:
                raw_data.append("No Deadline")

    if not raw_data:
        counts = {'No Data': 0}
    else:
        counts = Counter(raw_data)

    bar_fig = go.Figure(data=[go.Bar(
        x=list(counts.keys()),
        y=list(counts.values()),
        marker_color='#8A4FFF',
        width=0.3
    )])
    
    bar_fig.update_layout(
        margin=dict(t=20, b=20, l=40, r=20),
        height=200,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(tickmode='linear', tick0=0, dtick=1, gridcolor='rgba(243, 244, 246, 0.6)', tickfont=dict(color='#9CA3AF')),
        xaxis=dict(showgrid=False, tickfont=dict(color='#9CA3AF'))
    )
    
    bar_html = bar_fig.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})
    notifications = db.get_notifications(user_email)

    return render_template(
        "dashboard.html", 
        name=session.get("name"),completed=completed_count,incomplete=incomplete_count,overdue=overdue_count,total=total_tasks,
        donut_chart=donut_html,bar_chart=bar_html,active_filter=active_filter,notifications=notifications)

@app.route("/api/graph-data/<filter_type>")
def get_graph_data(filter_type):
    if "email" not in session:
        return {"labels": [], "values": []}, 401
        
    user_email = session.get("email")
    all_tasks = db.get_tasks(user_email)
    
    raw_data = []
    
    if filter_type == "category":
        raw_data = [t.get("category", "Uncategorized").strip() or "Uncategorized" for t in all_tasks]
        
    elif filter_type == "priority":
        raw_data = [t.get("priority", "Normal").strip() or "Normal" for t in all_tasks]
        
    elif filter_type == "deadline":
        raw_data = [t.get("deadline", "No Deadline").strip() or "No Deadline" for t in all_tasks]
        
    elif filter_type == "weekly":
        for t in all_tasks:
            date_str = t.get("deadline")
            if date_str:
                try:
                    task_date = datetime.strptime(date_str, "%Y-%m-%d")
                    raw_data.append(task_date.strftime("%A"))
                except ValueError:
                    raw_data.append("No Deadline")
            else:
                raw_data.append("No Deadline")

    if not raw_data:
        return {"labels": ["No Data Available"], "values": [0]}

    counts = Counter(raw_data)
    
    return {
        "labels": list(counts.keys()),
        "values": list(counts.values())
    }

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
            # get task title
            user_tasks = db.get_tasks(session["email"])
            task_title = ""
            for t in user_tasks:
                if t["id"] == task_id:
                    task_title = t.get("title", "")
                    break
            
            db.add_points(session["email"], 10)
            db.add_notification(session["email"], "Task Completed! 🎉", f"You completed '{task_title}' and earned 10 XP!", "success")
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

@app.route("/search")
def search():
    search = request.args.get("search", "").lower().strip()
    user_email = session.get("email")
    all_tasks = db.get_tasks(user_email)

    if search:
        results = [t for t in all_tasks if t['title'].lower().startswith(search)]
    else:
        results = []
    return render_template("task_cards.html", results=results)

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
                         name=session.get("name"),email=session["email"],joined_date=user.get("joined", "2025"),total_tasks=total_tasks,
                         completed_tasks=completed_tasks,points=points,streak=streak,profile_pic=user.get("pic"),bio=bio)

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

@app.route("/admin/user")
def manage_users():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    users = db.get_all_users()
    return render_template("manage_users.html", users=users)

#notifs route

@app.route("/api/notifications")
def get_notifications():
    if "email" not in session:
        return {"error": "not logged in"}, 401
    
    notifs = db.get_notifications(session["email"])
    unread_count = db.get_unread_count(session["email"])
    
    return {
        "notifications": notifs,
        "unread_count": unread_count
    }

@app.route("/api/notifications/mark_read/<int:notif_id>", methods=["POST"])
def mark_notification_read(notif_id):
    if "email" not in session:
        return {"error": "not logged in"}, 401
    
    db.mark_notification_read(session["email"], notif_id)
    return {"success": True}

@app.route("/api/notifications/mark_all_read", methods=["POST"])
def mark_all_notifications_read():
    if "email" not in session:
        return {"error": "not logged in"}, 401
    
    db.mark_all_read(session["email"])
    return {"success": True}

@app.route("/notifications")
def view_notifications_page():
    if "email" not in session:
        return redirect(url_for("login"))
    
    notifs = db.get_notifications(session["email"])
    return render_template("notifications.html", notifications=notifs)

@app.route("/notifications/delete/<int:notif_id>", methods=["POST"])
def delete_notification(notif_id):
    if "email" not in session:
        return redirect(url_for("login"))
    
    db.delete_notification(session["email"], notif_id)
    return redirect(url_for("dashboard"))

@app.route("/notifications/delete_all", methods=["POST"])
def delete_all_notifications():
    if "email" not in session:
        return redirect(url_for("login"))
    
    db.delete_all_notifications(session["email"])
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)