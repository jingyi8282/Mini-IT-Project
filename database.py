import json
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.user_file = "users.json"
        self.task_file = "tasks.json"
        self.load()
        
        self.admin_email = "admin@academicdiary.com"
        self.admin_password = "admin123"

    def load(self):
        # load users
        if os.path.exists(self.user_file):
            f = open(self.user_file, "r")
            self.users = json.load(f)
            f.close()
        else:
            self.users = {}

        # load tasks
        if os.path.exists(self.task_file):
            f = open(self.task_file, "r")
            data = json.load(f)
            f.close()
            self.tasks = {} if type(data) == list else data
        else:
            self.tasks = {}

    def save_users(self):
        f = open(self.user_file, "w")
        json.dump(self.users, f, indent=2)
        f.close()

    def save_tasks(self):
        f = open(self.task_file, "w")
        json.dump(self.tasks, f, indent=2)
        f.close()

    #user func
    
    def create_user(self, name, email, pw):
        if email in self.users:
            return False
        self.users[email] = {
            "name": name, "password": pw, "joined": str(datetime.now().date()),
            "points": 0, "streak": 0, "last_login": None, "pic": None, "bio": ""
        }
        self.tasks[email] = []
        self.save_users()
        self.save_tasks()
        return True

    def check_login(self, email, pw):
        user = self.users.get(email)
        if user and user["password"] == pw:
            for field in ["joined", "points", "streak", "last_login", "pic", "bio"]:
                if field not in user:
                    user[field] = 0 if field in ["points", "streak"] else (str(datetime.now().date()) if field == "joined" else None)
            self.save_users()
            return (email, user["name"], email)
        return None

    def reset_password(self, email, new_pw):
        if email not in self.users:
            return False
        self.users[email]["password"] = new_pw
        self.save_users()
        return True

    #points and streaks
    
    def update_streak(self, email):
        user = self.users.get(email)
        if not user:
            return
        today = str(datetime.now().date())
        last = user.get("last_login")
        if last == today:
            return
        user["streak"] = 1 if not last or last != str(datetime.now().date() - timedelta(days=1)) else user.get("streak", 0) + 1
        user["last_login"] = today
        self.save_users()

    def add_points(self, email, pts):
        if email in self.users:
            self.users[email]["points"] = self.users[email].get("points", 0) + pts
            self.save_users()

    def get_points(self, email):
        return self.users.get(email, {}).get("points", 0)

    def get_streak(self, email):
        return self.users.get(email, {}).get("streak", 0)

    def update_pic(self, email, filename):
        if email in self.users:
            self.users[email]["pic"] = filename
            self.save_users()
    
    def update_bio(self, email, bio):
        if email in self.users:
            self.users[email]["bio"] = bio
            self.save_users()
            return True
        return False
    
    def get_bio(self, email):
        return self.users.get(email, {}).get("bio", "")

    #tasks func
    
    def add_task(self, email, title, priority, deadline, cat):
        if email not in self.tasks:
            self.tasks[email] = []
        biggest = 0
        for t in self.tasks[email]:
            if t["id"] > biggest:
                biggest = t["id"]
        new_id = biggest + 1
        self.tasks[email].append({
            "id": new_id, "title": title, "priority": priority,
            "deadline": deadline, "category": cat, "status": "my_task"
        })
        self.save_tasks()
        return new_id

    def get_tasks(self, email):
        return self.tasks.get(email, [])

    def delete_task(self, email, task_id):
        if email in self.tasks:
            new = []
            for t in self.tasks[email]:
                if t["id"] != task_id:
                    new.append(t)
            self.tasks[email] = new
            self.save_tasks()

    def update_task(self, email, task_id, title, priority, deadline, cat):
        for t in self.tasks.get(email, []):
            if t["id"] == task_id:
                t["title"] = title
                t["priority"] = priority
                t["deadline"] = deadline
                t["category"] = cat
                self.save_tasks()
                return True
        return False

    def update_status(self, email, task_id, status):
        for t in self.tasks.get(email, []):
            if t["id"] == task_id:
                t["status"] = status
                self.save_tasks()
                return True
        return False

    #admin func
    
    def check_admin_login(self, email, password):
        if email == self.admin_email and password == self.admin_password:
            return True
        return False
    
    def get_admin_email(self):
        return self.admin_email
    
    def get_all_users(self):
        users_list = []
        for email, user_data in self.users.items():
            users_list.append({
                "username": user_data.get("name", ""),
                "email": email,
                "joined_date": user_data.get("joined", "N/A")
            })
        return users_list