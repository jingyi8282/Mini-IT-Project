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
        #load users
        if os.path.exists(self.user_file):
            f = open(self.user_file, "r")
            self.users = {}
            json.load(f)
            
            f.close()
        else:
            self.users = {}

        #load tasks
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

    #user data func
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

    # user points and streaks func
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

    #user tasks func
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

    #admin login func
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
    
    def delete_user_by_admin(self, email):
        if email in self.users:
            if email == self.admin_email:
                return False
           
            del self.users[email]
            if email in self.tasks:
                del self.tasks[email]
            self.save_users()
            self.save_tasks()
            return True
        return False
    

    #admin tasks func
    
    def get_all_users_tasks(self):
        all_tasks = []
        
        for email, tasks in self.tasks.items():
            user_name = self.users.get(email, {}).get("name", email)
            
            for task in tasks:
                all_tasks.append({
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "priority": task.get("priority"),
                    "deadline": task.get("deadline"),
                    "category": task.get("category"),
                    "status": task.get("status"),
                    "user_email": email,
                    "user_name": user_name
                })
        
        return all_tasks

    def delete_any_task(self, task_id):
        for email, tasks in self.tasks.items():
            for i, task in enumerate(tasks):
                if task.get("id") == task_id:
                    del self.tasks[email][i]
                    self.save_tasks()
                    return True
        return False

    def get_all_users_list(self):
        users_list = []
        for email, user in self.users.items():
            users_list.append({
                "email": email,
                "name": user.get("name", email)
            })
        return users_list

    def get_task_stats(self):
        total = 0
        completed = 0
        pending = 0
        
        for tasks in self.tasks.values():
            total += len(tasks)
            for task in tasks:
                if task.get("status") == "completed":
                    completed += 1
                else:
                    pending += 1
        
        completion_rate = round((completed / total) * 100) if total > 0 else 0
        
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "completion_rate": completion_rate
        }

    #notifs stuffs
    
    def add_notification(self, email, title, msg, notif_type=None):
        #add a notif for user
        try:
            f = open("notifications.json", "r")
            data = json.load(f)
            f.close()
        except:
            data = {}
        
        if email not in data:
            data[email] = []
        
        # get next id number
        if len(data[email]) == 0:
            new_id = 1
        else:
            biggest = 0
            for n in data[email]:
                if n["id"] > biggest:
                    biggest = n["id"]
            new_id = biggest + 1
        
        new_notif = {
            "id": new_id,
            "title": title,
            "message": msg,
            "type": notif_type,
            "read": False,
            "time": str(datetime.now())
        }
        
        data[email].append(new_notif)
        
        f = open("notifications.json", "w")
        json.dump(data, f, indent=2)
        f.close()
    
    def get_notifications(self, email):
        try:
            f = open("notifications.json", "r")
            data = json.load(f)
            f.close()
            
            if email in data:
                # reverse so newest shows first
                notifs = data[email][::-1]
                return notifs
            return []
        except:
            return []
    
    def get_unread_count(self, email):
        try:
            f = open("notifications.json", "r")
            data = json.load(f)
            f.close()
            
            if email not in data:
                return 0
            
            count = 0
            for n in data[email]:
                if not n["read"]:
                    count = count + 1
            return count
        except:
            return 0
    
    def mark_notification_read(self, email, notif_id):
        try:
            f = open("notifications.json", "r")
            data = json.load(f)
            f.close()
            
            if email in data:
                for n in data[email]:
                    if n["id"] == notif_id:
                        n["read"] = True
                        break
            
            f = open("notifications.json", "w")
            json.dump(data, f, indent=2)
            f.close()
        except:
            pass
    
    def mark_all_read(self, email):
        try:
            f = open("notifications.json", "r")
            data = json.load(f)
            f.close()
            
            if email in data:
                for n in data[email]:
                    n["read"] = True
            
            f = open("notifications.json", "w")
            json.dump(data, f, indent=2)
            f.close()
        except:
            pass
    
    def delete_notification(self, email, notif_id):
        #delete one notif
        try:
            f = open("notifications.json", "r")
            data = json.load(f)
            f.close()
            
            if email in data:
                new_list = []
                for n in data[email]:
                    if n["id"] != notif_id:
                        new_list.append(n)
                data[email] = new_list
            
            f = open("notifications.json", "w")
            json.dump(data, f, indent=2)
            f.close()
        except:
            pass
    
    def delete_all_notifications(self, email):
        #delete all notifs
        try:
            f = open("notifications.json", "r")
            data = json.load(f)
            f.close()
            
            if email in data:
                data[email] = []
            
            f = open("notifications.json", "w")
            json.dump(data, f, indent=2)
            f.close()
        except:
            pass